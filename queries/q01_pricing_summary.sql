-- One quarter of shipments: partition pruning skips every other month.
SELECT returnflag,
       linestatus,
       sum(quantity)                         AS sum_qty,
       sum(extendedprice * (1 - discount))   AS revenue,
       avg(discount)                         AS avg_disc,
       count(*)                              AS line_count
FROM {lineitem}
WHERE shipdate >= DATE '1995-01-01'
  AND shipdate <  DATE '1995-04-01'
GROUP BY returnflag, linestatus
ORDER BY returnflag, linestatus
