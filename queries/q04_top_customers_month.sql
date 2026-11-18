-- Top customers for a single month, joined with dimension tables.
SELECT c.name,
       n.name               AS nation,
       sum(o.totalprice)    AS spend,
       count(*)             AS orders
FROM {orders} o
JOIN {customer} c ON c.custkey = o.custkey
JOIN {nation}   n ON n.nationkey = c.nationkey
WHERE o.orderdate >= DATE '1997-03-01'
  AND o.orderdate <  DATE '1997-04-01'
GROUP BY c.name, n.name
ORDER BY spend DESC
LIMIT 10
