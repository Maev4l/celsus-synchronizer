CREATE TABLE IF NOT EXISTS "library"
(
    id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(512) ,
    CONSTRAINT library_id_key UNIQUE (id)
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;




INSERT INTO "library" ("id", "user_id", "name", "description")	VALUES ('af9da085-4562-475f-baa5-38c3e5115c09', 'user1', 'My Library A', 'My Library A description');
INSERT INTO "library" ("id", "user_id", "name", "description")	VALUES ('18a10d9d-4328-4404-8a65-ec1077113bea', 'user1', 'My Library B', 'My Library B description');
INSERT INTO "library" ("id", "user_id", "name", "description")	VALUES ('73b57d71-4938-45cc-9880-51db8ebf3e7a', 'user2', 'My Library Name', 'My Library description');


