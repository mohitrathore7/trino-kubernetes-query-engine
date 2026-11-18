-- Join: the month filter on orders becomes a dynamic filter on lineitem.orderkey.
SELECT o.orderpriority,
       count(DISTINCT o.orderkey) AS late_orders
FROM {orders} o
JOIN {lineitem} l ON l.orderkey = o.orderkey
WHERE o.orderdate >= DATE '1996-07-01'
  AND o.orderdate <  DATE '1996-08-01'
  AND l.commitdate < l.receiptdate
GROUP BY o.orderpriority
ORDER BY o.orderpriority
