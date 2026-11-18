-- Narrow lookup: one month + one ship mode + one order-key range.
SELECT shipmode,
       count(*)           AS lines,
       sum(extendedprice) AS value
FROM {lineitem}
WHERE shipdate >= DATE '1998-06-01'
  AND shipdate <  DATE '1998-07-01'
  AND shipmode = 'AIR'
  AND orderkey BETWEEN 1000000 AND 2000000
GROUP BY shipmode
