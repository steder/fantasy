-- for looking up the best players from a cost efficiency standpoint
-- in the IND / PHI game on 2014/9/15
-- you might try a query like this:
select name, team, position, salary, standard, (standard / (salary :: numeric / 1000)) as standard_efficency
from players
where salary > MONEY(0)
AND year = 2014
AND week = 2
AND team in ('IND', 'PHI')
order by (standard / (salary :: numeric / 1000)) DESC;
