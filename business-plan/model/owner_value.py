# Owner-side value model (ILS/month, ex-VAT). All drivers are assumptions to be measured in pilots.
def owner_value(tables=12, covers_per_table_day=13, days=26, check=40, gm=0.68,
                extra_item_rate=0.005, extra_item_price=16,
                issue_rate=0.002, save_share=1/3, saved_value=150):
    covers = tables*covers_per_table_day*days
    revenue = covers*check
    extra_orders = covers*extra_item_rate*extra_item_price*gm
    recovery = covers*issue_rate*save_share*saved_value
    base = extra_orders+recovery
    # upside: rating via Luca 5-9% per star; assume +0.1 star over ~12 months
    upside_lo, upside_hi = revenue*0.005, revenue*0.009
    return dict(tables=tables, covers=covers, revenue=revenue, extra=extra_orders, recovery=recovery,
                base=base, per_table=base/tables, up_lo=upside_lo, up_hi=upside_hi,
                price10=base*0.10, price20=base*0.20)
for t in (8,12,20,30):
    r=owner_value(tables=t); print({k:round(v) for k,v in r.items()})
