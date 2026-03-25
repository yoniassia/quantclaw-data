-- Allow pipeline user to write eToro (and other) bridge rows into platinum_records.
-- Run as a superuser, e.g. psql -U postgres -d quantclaw_data -f 004_platinum_records_grants.sql

GRANT SELECT, INSERT, UPDATE ON platinum_records TO quantclaw_user;
GRANT USAGE, SELECT ON SEQUENCE platinum_records_id_seq TO quantclaw_user;
