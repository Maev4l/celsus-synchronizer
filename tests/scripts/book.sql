CREATE TABLE IF NOT EXISTS "book"
(
    id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL,
	  library_id VARCHAR(36) NOT NULL,
    title VARCHAR(100) NOT NULL,
    description VARCHAR(1024) ,
	  isbn10 VARCHAR(30),
	  isbn13 VARCHAR(30),
	  thumbnail TEXT,
	  authors VARCHAR(1024) ARRAY,
	  tags VARCHAR(1024) ARRAY,
	  hash VARCHAR(64),
    language VARCHAR(36) NOT NULL DEFAULT('french'),
    CONSTRAINT book_id_key UNIQUE (id)
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

-- 1. Simple test case for user1
INSERT INTO "book"("id", "user_id", "library_id", "title", "description", "isbn10", "isbn13", "thumbnail", "authors", "tags", "hash")
  VALUES ('1', 'user1', 'af9da085-4562-475f-baa5-38c3e5115c09', 'Book Title1', 'Book Desc', 'Book isbn10', 'Book isbn13', 'Book thumbnal', ARRAY['Book authors'], ARRAY['Book tags'], 'hash-1.0');
INSERT INTO "book"("id", "user_id", "library_id", "title", "description", "isbn10", "isbn13", "thumbnail", "authors", "tags", "hash")
  VALUES ('2', 'user1', 'af9da085-4562-475f-baa5-38c3e5115c09', 'Book Title2', 'Book Desc', 'Book isbn10', 'Book isbn13', 'Book thumbnal', ARRAY['Book authors'], ARRAY['Book tags'], 'hash-2.1');
INSERT INTO "book"("id", "user_id", "library_id", "title", "description", "isbn10", "isbn13", "thumbnail", "authors", "tags", "hash")
  VALUES ('3', 'user1', 'af9da085-4562-475f-baa5-38c3e5115c09', 'Book Title3', 'Book Desc', 'Book isbn10', 'Book isbn13', 'Book thumbnal', ARRAY['Book authors'], ARRAY['Book tags'], 'hash-3.0');

INSERT INTO "book"("id", "user_id", "library_id", "title", "description", "isbn10", "isbn13", "thumbnail", "authors", "tags", "hash")
  VALUES ('500', 'user2', '73b57d71-4938-45cc-9880-51db8ebf3e7a', 'Book Title500', 'Book Desc', 'Book isbn10', 'Book isbn13', 'Book thumbnal', ARRAY['Book authors'], ARRAY['Book tags'], 'hash-500.0');
