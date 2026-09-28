from final import BASE, simulate, per_customer
base = simulate(BASE,24)
print('base 24m', {k:round(v) for k,v in base.items()})
tests = [('price',99,169),('churn',5,2),('close',15,35),('loss',40,10),('unit',14,6),('newpm',2,5),('free',2,0),('setup',0,390)]
for k,lo,hi in tests:
    a=simulate(dict(BASE,**{k:lo}),24); b=simulate(dict(BASE,**{k:hi}),24)
    print(f"{k:6} {lo}->{hi}: MRR24 {a['mrr']:.0f}..{b['mrr']:.0f}  cum_cash24 {a['cum_cash']:.0f}..{b['cum_cash']:.0f}  swing {b['cum_cash']-a['cum_cash']:.0f}")
for mo in (12,24,36):
    s=simulate(BASE,mo); print(mo, round(s['cash']/s['hours']))
