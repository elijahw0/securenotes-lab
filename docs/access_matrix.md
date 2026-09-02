401 for missing or invalid token. 403 for wrong role. 404 for ownership failures, so that resource existence isn't leaked to non-owners.

| Endpoint  | Method | Authentication?  | Input Validation | Rule | Role | No token | Wrong role | Broken rule/not owner |
| :---- | :---- | :---- | :---- | :---- | :---- | :---- | :---- | :---- |
| /health | GET | No | — | —- | Any or —- | 200 | – | —- |
| /api/register | POST | No | Username and password | —- | —- | 201 | — | 400 |
| /api/login | POST | No | Valid Username and password | — | any | 200 | — | 401 |
| /api/logout | POST | YES | —- | Need to invalidate token, active user session  | any | 401 (token expires right after check) | — | Doesnt check if token belongs to user |
| /api/profile | GET | YES | —- | Only get your own profile, valid token | any | 401 | — | —- |
| /api/users/\<id\> | GET | YES | Valid user | Only retrieve user info if valid admin | Admin | 401 | 403 | 404 |
| /api/notes/\<id\> | PUT | YES | Need any edits | Edit note if owner | Any (as long as owner) | 401 | —- | 404 |
| /api/notes/\<id\> | DELETE | YES | —- | Delete note with valid token and ownership | Any (owner) | 401 | — | 404 |
| /api/notes/\<id\> | GET | YES | —- | Retrieve note if ownership and valid token | Any owner | 401 | —- | 404 |
| /api/notes/ | POST | YES | Need at least a note body | Creates note if valid user | Any owner | 401 | —- | 400 |
| /api/notes/ | GET | YES | —- | Retrieve all notes that belong to its user. | Any owner | 401 | —- | —- |
| /api/admin/users | GET | YES | —-- | Retrieve all users | Admin | 401 | 403 | —- |

