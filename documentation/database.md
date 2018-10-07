# MySQL usefuls 

## Security

Creating a new user
```
create user "<username>"@"<hostname>" identified by "<password>";
```
`<hostname>` can be `%` to allow access from all computers.

Deleting a user
```
drop user <username>;
```

List all users
```
select User from mysql.user;
```

To show permissions for a user
```
show grants for <username>;
```

To grant read access to a user for a certain table in a database
```
grant select on <database>.<tablename> to <username>;
```

To revoke all privileges
```
revoke all, grant option from <username>;
```
