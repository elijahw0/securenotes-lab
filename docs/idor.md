# IDOR/BOLA Vulnerability

# IDOR/BOLA Vulnerability

Insecure Direct Object Referencing (IDOR) and Broken Object Level Authorization (BOLA) both refer to the same issue. IDOR is the older OWASP web term, and BOLA is what the OWASP API Security Top 10 calls it. It happens when a user changes the object identifier in the curl, or crafts their own request to the api, and the application returns that object without checking whether the user is allowed to access it.

Being able to see or guess an object ID is not the vulnerability on its own. The vulnerability is insufficient authorization when determining access to resources. If the application does not properly check if a certain user should access this specific resource, any user can reach any object just by changing the ID. In this application that goes against confidentiality (reading notes), integrity (editing notes), and availability (deleting notes).

The reason it exists in this application lies within the code for the RUD endpoints. When retrieving, updating, or deleting a note by its ID, it fetches the note from the database without checking the owner_id attached to the note. The owner_id is a foreign key that points to the id in the users table, and the application never compares the note's owner_id to the id of the user making the request. Since that check doesn't happen, alice is able to read, edit, and delete bob's notes using her own valid token, and the application does not check that alice is not able to do that.

The baseline branch fixes this by adding `and owner_id = ?` to every note query, so the database only returns the note if it belongs to the requesting user. If it doesn't, the application returns 404 instead of 403, so the response doesn't confirm that the note exists.

Additionally, since all note ids are sequential, attackers can basically brute force note ids and retrieve all notes without being authorized to as long as the authorization check is missing. The fix is the authorization check on every resource. Universally Unique Identifiers (UUIDs), long random IDs, add defense in depth by making IDs hard to guess, but they don't replace the check, since a UUID can still leak through a shared link, a log, or a screenshot.

On the detection side, baseline logs a note_access_denied event every time a user requests a note they don't own, so a user hitting many note ids in a row stands out in the logs.
