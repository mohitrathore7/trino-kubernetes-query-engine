-- TPC-H Q6 style: one year + range filters pushed down to Parquet row groups.
SELECT sum(extendedprice * discount) AS revenue
FROM {lineitem}
WHERE shipdate >= DATE '1994-01-01'
  AND shipdate <  DATE '1995-01-01'
  AND discount BETWEEN 0.05 AND 0.07
  AND quantity < 24
