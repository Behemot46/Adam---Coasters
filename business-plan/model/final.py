# Final calibrated model (ILS ex-VAT). Mirrors the JS calculator in the artifact.
BASE = dict(newpm=3.5, price=129, setup=250, free=1, churn=3.0, tags=16, loss=20.0,
            unit=9.0, umin=5.0, hourly=50.0, close=25.0, fixed=450.0)
DEMO_CASH=12; FUEL=15; VISIT_MIN=65; INSTALL_MIN=90; SUPPORT_MIN=20; MAIL=25; MAIL_PER_YR=2; PROC=0.02; VAR_HOST=2

def per_customer(p):
    unit_labor = p['umin']/60*p['hourly']
    repl_units_m = p['tags']*p['loss']/100/12
    repl_cash_m = repl_units_m*p['unit'] + MAIL*MAIL_PER_YR/12
    repl_hours_m = repl_units_m*p['umin']/60 + MAIL_PER_YR/12*0.25
    sup_hours_m = SUPPORT_MIN/60
    cash_contrib = p['price']*(1-PROC) - repl_cash_m - VAR_HOST
    econ_contrib = cash_contrib - (repl_hours_m+sup_hours_m)*p['hourly']
    visits = 100/p['close']
    acq_cash = visits*(DEMO_CASH+FUEL); acq_hours = visits*VISIT_MIN/60
    onb_cash = p['tags']*p['unit'] + FUEL; onb_hours = (p['tags']*p['umin']+INSTALL_MIN)/60
    cac_cash = acq_cash+onb_cash-p['setup']
    cac_econ = cac_cash + (acq_hours+onb_hours)*p['hourly']
    return dict(cash_contrib=cash_contrib, econ_contrib=econ_contrib, repl_cash_m=repl_cash_m,
                repl_hours_m=repl_hours_m, cac_cash=cac_cash, cac_econ=cac_econ,
                acq_hours=acq_hours, onb_hours=onb_hours, hours_m=repl_hours_m+sup_hours_m,
                payback_cash=(cac_cash/cash_contrib + p['free']) if cash_contrib>0 else float('inf'),
                payback_econ=(cac_econ/econ_contrib + p['free']) if econ_contrib>0 else float('inf'),
                be_cash=p['fixed']/cash_contrib, be_econ=p['fixed']/econ_contrib)

def simulate(p, months=12):
    c=per_customer(p); cohorts=[]; cum_cash=cum_econ=0
    for m in range(1,months+1):
        for k in cohorts: k['n']*=(1-p['churn']/100); k['age']+=1
        cohorts.append({'n':p['newpm'],'age':0})
        active=sum(k['n'] for k in cohorts); paying=sum(k['n'] for k in cohorts if k['age']>=p['free'])
        rev_net = paying*p['price']*(1-PROC)
        # replacement + hosting on all active, acquisition/onboarding on new
        cash = rev_net - active*(c['repl_cash_m']+VAR_HOST) - p['newpm']*c['cac_cash'] - p['fixed']
        hours = active*c['hours_m'] + p['newpm']*(c['acq_hours']+c['onb_hours'])
        econ = cash - hours*p['hourly']
        cum_cash+=cash; cum_econ+=econ
    return dict(active=active, paying=paying, mrr=paying*p['price'], cash=cash, econ=econ, hours=hours,
                cum_cash=cum_cash, cum_econ=cum_econ)

if __name__=='__main__':
    c=per_customer(BASE); print({k:round(v,1) for k,v in c.items()})
    for mo in (12,24,36):
        print(mo, {k:round(v) for k,v in simulate(BASE,mo).items()})
    print('\nSensitivity: cash contribution / econ contribution per customer per month')
    for loss in (10,20,40):
        row=[]
        for price in (89,149,199):
            tags={89:11,149:17,199:27}[price]
            p=dict(BASE, loss=loss, price=price, tags=tags)
            cc=per_customer(p); row.append(f"{price}:{cc['cash_contrib']:.0f}/{cc['econ_contrib']:.0f} repl {cc['repl_cash_m']:.1f}")
        print(loss, row)
    print('\nVisit-based replacement (2 visits/yr, 1h + fuel each) at loss 20/40, 17 tags')
    for loss in (20,40):
        units=17*loss/100/12
        cash=units*9 + 2*15/12; hrs=units*5/60 + 2*1/12
        print(loss, round(cash,1), round(hrs*50,1), 'total', round(cash+hrs*50,1))
    print('\nMake vs buy crossover hourly: home cash c_h + min*H/60 = outsourced c_o')
    for label,ch,co,mins in (('100',8.5,13.5,5),('500',5.75,9.0,5)):
        print(label, 'H* =', round((co-ch)/mins*60,1))
    print('\nInjection mold payback units: tooling ILS / saving per unit')
    for tool in (1500*3.05, 4000*3.05):
        for save in (4.0, 6.0):
            print(round(tool), save, round(tool/save))
    # scenarios for SOM
    for npm in (2,3.5,5):
        s=simulate(dict(BASE,newpm=npm),36); print('newpm',npm,{k:round(v) for k,v in s.items()})
