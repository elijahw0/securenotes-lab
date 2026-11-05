# Broken Function Level Authorization 

# Broken Function Level Authorization 

Broken Function Level Authorization (BFLA) refers to when a function in the application doesn't properly check permissions for an action, process or function, unlike IDOR/BOLA, which is for an object. 

In this case, BFLA is found in the /api/admin/users endpoint that is supposed to be an endpoint accessible for only admin accounts. When sending a GET request to this endpoint, you are able to list all registered users, their role, ids, and when they were created. Under normal conditions, this action is only reserved for admins, but with the flaw present, the endpoint fails to verify if the token presented belongs to an admin user. 

The endpoint still checks that the token is valid and that you are authenticated, but it no longer checks the user's role and what they're allowed to do. In the code, `@require_auth(role="admin")` was changed to `@require_auth()`.

Therefore, any registered user can dump and view all registered users and see their permissions, which an threat actor can use to narrow their attack approach, now being able to see all registered accounts so they don't have to guess usernames, and can focus all their resources on brute forcing the passwords of admin accounts. 

Since the application also has no rate limiting on login, that brute force is actually feasible, so BFLA hands the attacker a list of targets with unlimited tries. It doesn't leak passwords, but it is full account enumeration.

The baseline branch fixes this with `@require_auth(role="admin")`, which returns 403 Forbidden to non-admin users and logs the attempt, so a regular user probing admin endpoints shows up in the logs.

STR**I**D**E**: Elevation of Privilege, Information Disclosure.