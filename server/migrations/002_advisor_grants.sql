-- Grant permissions on advisor tables to the application user.
-- Run this as a PostgreSQL superuser (e.g. postgres) if you get "permission denied for table advisor_conversations".
-- Replace dux_user with the username from your DATABASE_URL if different.

GRANT ALL PRIVILEGES ON TABLE advisor_conversations TO dux_user;
GRANT ALL PRIVILEGES ON TABLE advisor_messages TO dux_user;
GRANT USAGE, SELECT ON SEQUENCE advisor_conversations_id_seq TO dux_user;
GRANT USAGE, SELECT ON SEQUENCE advisor_messages_id_seq TO dux_user;
