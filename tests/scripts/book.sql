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
    language VARCHAR(36) NoT NULL DEFAULT('french'),
    CONSTRAINT book_id_key UNIQUE (id)
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

CREATE TABLE IF NOT EXISTS "books_search"
(
	id VARCHAR(36) NOT NULL,
	document TEXT,
	language TEXT
)
WITH (
	OIDS = FALSE
)
TABLESPACE pg_default;

CREATE OR REPLACE FUNCTION "celsus_core"."books_search_refresh"() RETURNS TRIGGER
AS $books_search_refresh$
	BEGIN
		IF (TG_OP = 'DELETE') THEN
			DELETE FROM "celsus_core"."books_search" WHERE "id" = OLD."id";
		ELSIF (TG_OP = 'UPDATE') THEN
			UPDATE "celsus_core"."books_search" 
			SET "document" = to_tsvector('simple',unaccent(NEW."title")) || to_tsvector('simple',unaccent(array_to_string(NEW."authors",' '))),
			"language" = NEW."language"
			WHERE "id"=NEW."id";
		ELSIF (TG_OP = 'INSERT') THEN
			INSERT INTO "celsus_core"."books_search" ("id", "document", "language") 
			VALUES (NEW."id",
					to_tsvector('simple',unaccent(NEW."title")) || to_tsvector('simple',unaccent(array_to_string(NEW."authors",' '))),
					NEW."language"
				   );
		END IF;
		RETURN NULL;
	END;
$books_search_refresh$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS books_search_indexer ON "celsus_core"."book";
CREATE TRIGGER books_search_indexer
AFTER INSERT OR UPDATE OR DELETE ON "celsus_core"."book"
	FOR EACH ROW EXECUTE PROCEDURE "celsus_core"."books_search_refresh"();

CREATE INDEX IF NOT EXISTS idx_fts_books ON "celsus_core"."books_search" USING gin(to_tsvector('simple',"document"));

-- Belong to library with id 6 (for retrieval test)
INSERT INTO "book"("id", "user_id", "library_id", "title", "description", "isbn10", "isbn13", "thumbnail", "authors", "tags", "hash")
  VALUES ('1', 'user4', '6', 'Book Title1', 'Book Desc', 'Book isbn10', 'Book isbn13', 'Book thumbnal', ARRAY['Book authors'], ARRAY['Book tags'], 'Book hash');
INSERT INTO "book"("id", "user_id", "library_id", "title", "description", "isbn10", "isbn13", "thumbnail", "authors", "tags", "hash")
  VALUES ('2', 'user4', '6', 'Book Title2', 'Book Desc', 'Book isbn10', 'Book isbn13', 'Book thumbnal', ARRAY['Book authors'], ARRAY['Book tags'], 'Book hash');

-- Belong to library with id 4 (for deletion test)
INSERT INTO "book"("id", "user_id", "library_id", "title", "description", "isbn10", "isbn13", "thumbnail", "authors", "tags", "hash")
  VALUES ('3', 'user2', '4', 'Book Title', 'Book Desc', 'Book isbn10', 'Book isbn13', 'Book thumbnal', ARRAY['Book authors'], ARRAY['Book tags'], 'Book hash');

-- Belong to library with id 7 (for deletion test)
INSERT INTO "book"("id", "user_id", "library_id", "title", "description", "isbn10", "isbn13", "thumbnail", "authors", "tags", "hash")
  VALUES ('4', 'user5', '7', 'Book Title', 'Book Desc', 'Book isbn10', 'Book isbn13', 'Book thumbnal', ARRAY['Book authors'], ARRAY['Book tags'], 'Book hash');

-- Belong to user 7 (for update book test)
INSERT INTO "book"("id", "user_id", "library_id", "title", "description", "isbn10", "isbn13", "thumbnail", "authors", "tags", "hash")
  VALUES ('2894d16a-78fe-4dfc-a2b0-0a080898a490', 'user7', '73b57d71-4938-45cc-9880-51db8ebf3e7a', 'Book Title', 'Book Desc', 'Book isbn10', 'Book isbn13', '', ARRAY['Book authors'], ARRAY['Book tags'], 'Book hash');

-- Belong to user 9 (for update book test with thumbnail)
INSERT INTO "book"("id", "user_id", "library_id", "title", "description", "isbn10", "isbn13", "thumbnail", "authors", "tags", "hash")
  VALUES ('341e5d68-4682-4b91-9058-200a60d4ad75', 'user9', '979ed879-b3c0-40fa-83ff-5f4442052217', 'Book Title', 'Book Desc', 'Book isbn10', 'Book isbn13', '/9j/4AAQSkZJRgABAQAAAQABAAD/2wCEAAkGBxITEhUQEhMSFRUVEBAQEhAQDw8QEBUQFRUWFhUVFhUYHSggGBolGxUVITEhJSkrLi4uFx8zODMtNygtLisBCgoKDg0OGhAQGi0lHSItLSsrLS0tLS0rLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLSstLS0rLSsrNy0tK//AABEIAMEBBQMBIgACEQEDEQH/xAAbAAEAAgMBAQAAAAAAAAAAAAAAAQQDBQYCB//EADsQAAIBAgQDBQYEBAYDAAAAAAABAgMRBCExQQUSUQYTYXGRMkKBobHBIlLR4WJyk/AHFSNTgpIWM2P/xAAaAQEAAwEBAQAAAAAAAAAAAAAAAgMEAQUG/8QAIxEAAgIBBAIDAQEAAAAAAAAAAAECEQMEEiExE0EUIlFhBf/aAAwDAQACEQMRAD8A+4gAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAgAEggAEggAEggAEggAEggAEggAEggAEggAEggAEggAEggAEggAEggAEggAEggAEggkAAgAEggkAAAAAgAEkHmpUSzZVqYpvTLx3ISyRj2SUWyzUqpasryxfRFVvzMU4N3vptZ5mSeok+i6OJey3Ks+pgqV2t36sp1sbytJ3zyyR6lV32Mss7fsuWKixHHyW/rmW8PxKMsnk+uxpJ1EVp1WRhrJwf6TenjJHY3JNHwbiV33Un/I/sbw9bFlWSO5GHJBwdMAgwYrGQgvxP4LNk20lbIpN8IsEFBY9vOMfUlY+3tR9GVeeH6S8ci+DHSrRlmmZC1NMgAAdAAAAAAAAAAAAABAAJBAAJBAAJKeKxijks39DDxTHcv4I6vV9EaqjK7yd8/mYdRq9j2x7NOLBa3Pouc7k7ttmaC62MKujxWrePwMTye2Xbb4RllM8TqW6/Ap974mKVfxKZahFixFvFQjJNGthiNV0dmKuK1RqZVmpt3yf1RW8ikXRhXZsZ1iu8QVp4haIqzq2zKGy1IszxcoyUk/ZakvNH0XDVVOEZr3oqXqfKJ1rn0ns7O+GpNv3Fuep/m5bbiYtbDhSLWPxKgvF6GiUnKV31ue+MYm9VrZJL7sx0KiK9VqXPK4p8IYcW2F+2W+/sYZ4m5Xq1DDOoZZ5n0WxxotRxTi7pm9wOMVRX3WqOU7wz4HFuErr4rqjRpNW4Sp9EM2BSXHZ1wPFOakk1o1c9nvJ2eYAQSAAAAAAAAAAAQACQQACSGwRNZBg5adTnm5Pd3/AGM1C+fn8inU/C3fxT+BOHrppOLy6nzLm9zs9jb9eDZ1KiNdXrkVqzNXXrS5tMrO73vtb5leTI30dx46LsqpVrV+hilVK1Wtvcotl1GSrMpVax4qV7lWpNvL5kXOiVGWNTr1MdauYpzsVq1ZHN52jI6vTd5ebO/w01Tpwg9opPz3OJ7PYfmqd7L2YZro5bemp09SspZGrA5RTa7KsiUuGeKle9SWfvF+jPJGhxUu7q8t9VFp+a/U2WCqt+NkU2/K0ScfqbCaK1SEvyy9GXKeJULXXors2EKqay6aM1rTqS7M7yOPo5tqS1jJecWhTqHRTkjBVoQlrFeayZ1YEumc819otdn8XdOm9s15bm5RzWDw/dzUovK+afQ6KE0807+R7OkncKfaMGeKUrR7BANZQSCAASCAASCAASCAASCAwAeKlRLVlbFY1Ryjm/kUJTcnd5mbLqYw4XZdDE3yzXcbS5+ZaS1y941tKXI7ZKPupfM39eCaaksmszmOIS5Ha91s/szwtSuXJez08D+u1lqpXKlaqupr58RS3KOI4iupj3mijY4jEbIrTrXNNV4iVJ8T8Rtk/QtI3VXEpMqVseluaLF8WtuXOz/AquLfPO8aV/KUvLovEsWndXLgjv8Aw9PHym+SnGUpdIptmw4f2fxU2nUjyx3XMnJ+GWh3PCeC06UVGMUl4LXzNoqFtC6GJVwit5Dn8JwyUYqOUUtEsya2CktJK/Rpq/x0N5ClZO7bzbu3cqYjpuW7UkcjK2cfxutKMouaaaus+h0/BXaEb68qb83sVcfQ504ztKO6e3ke61RpLkWhldKVltWqOgpKLtoeZyayyKeHxFkeK+Luy7zJR/pR43ZZnXJVc1ksQO/K1lbJeM2kaxYo4lxeTt4bGnjWLEKpfDNKPRXLGn2dNhcapZPJ/ItHKRqm44bxDm/BJ57PqetptXv+suzFlwbeUbQBA3GYAAAAAAAAAGv4njeRcq9p/JF6crJt7K5zFarzycn1MWt1HihS7Zo0+Pe7fSPdJtu7LFzxFJK5g77c8uLpfY2NX0ZK0HLK9vDc11fhUZa3fx/Qu82XNZt/Yy4dye2W3U7KEJM6pOKs5uv2XoyzcZLynP8AU0fEexas3Tqzi9ua0on0erTT2NdVgtCMsewnHLfZ8V4zw3EYd2qabTXsv9GaWpVl1PtnEsLCcXTkk01o1kz5P2n4Q8PUss4Su4N7fwsnimm69nZJpWR2V4O8TXUXfkjaU3npfKPxPtfDsKoxUYpJJJJaKxyH+HPDeShztfim+d+Xu/I7zDwbzVirJLfkr0g/rEtwpqxinGxNWfLmV54gnKSXBRGLZFUp1pGbmcskWKWBWrzK9rn0XKSj2aHEqcsoxbfRK5kwfDa7X4ko+cr/AEOmhSS0SJlTv6klpY+2Repfo0UuE1N6iXhyt/c8R4HP/cv/AMH+p0XILon8bH+EPkTOefBqmvPH0ZhqcNqx2T8nn8zpWzBUeZF6fGuiSzSfZzPM07NNPxyMsZ53NviIRkrSSf1XkzS4zDuGavZ6dV4MqljrosUrLUahixVdxjzR1Was7GGlM9VHdZiNrk5wdnwfHd7TTftJLmX3Ngcd2fxHLVS2l+F/HT52OwPf0uXyQt9nm54bJ8EgA0FIAAAAIAK/EX/pz/lZy/K2mk7X3R11WmpRcXo016nKTi4Nwllb+0zyP9ODuMvXRu0klTRPeWSjrlmz1FXRjlr8F9D2tPqee5OzUy3QiWeYwUlbO5gxmOUcvqXqSiilxcmWqtZGvrzPHfqWj3KOMrN5Xt0sU5MrZbDHRhxMtc8zku1lBVaTT2lGSfjfP5NnRV6+z1tmcz2gr2pzf8Lf1Koye5V2X1wdHwjEpQio9F6G8wePzs2cLwDHXis9jqeG4eUnzvJbdX4kY2mdltaNtiK15W5tdF4IyUKXgKVEuwijRCNu2Z5SpUhCkZ4IxxdiJVjSmkUO2Z4Zav7ZBzKEsRdnuVT187EfN+Dx/pkq57nhzstczFUqGLnZVLKWRgZed3Mffu+drbGCcpXVmrZ3Vs/Cx4lJ38LfMqeRligjPUmU61RNOMtGJV1e1zFUgnqdjK2dqjXzqcr5X1sZYyuYMTP/AFGvL6IyUWXOJCzY8Ovzx/mj9TukcTwinerBb3XotTtkenoVUWYtS7kiQAbjMAAAAQAAzW8Z4eqkbrKSWT2a6M2REo3RCcFONMlGTi7RylKLSs1mkl6ZHts2uNwWV18TWTgfPanC8c/4enjyKash1NijisHGp7V9etixiaTasna2ZTliHFLm3KrvgtjH8PdWySS0RQrx3LlZ3V1fyRrsYpX8N+pGUWySNdjnfK765HJdrMUlDk3llbw3OuxyUYuUnZJXb8F4nzDimKdao57ZqK6R2LtNie7c/RzJPijtv8NuFSqxdWf/AK4y5Y/xyW3kj6XTitEazs7hY0sPSpR0VKPq1eTfm2bajkRlJSmyDVIz04GWVkYO9Mc65buSKtrZnc0Va02jzOp0KuLquz1fgiuU7JxhyYMLXUrvxZsO8NFwtpNyzzektV8DaKoVdF0kZZ1LnmUzzKRjckc5OUZOdGOpMxuOd+tr/DQxTzOUzp5qPcxOWd0/AySWZjSu8voWwiRbKHFZctRP80E/im0ThK13tbKxp+1+KnGtTpwje1K8nfRybsvRfMu9mVJyTqRv0Xu/uboY2+CiUkj6B2ZwWXeyW1o/dnQGu4dNtI2R62KChGkefkk5StgAFhAAAAAgAEggAHmZo+I00nzL4o3k0a/E0bmXUY1NUy7DLa7NL3y+x4q8u6Xomesbwtt3i2n1TNVXoYmOnLLzTTPJnpZJ8HoRyxZaqTS/ZFHG4mEYuU2klrd7GuxVTG6RjBeNpSNLX4FiarvVlKXh7q8kIYZPs65JGp7ScWeIfd07qmnm95tafA1VDhMnsd3gOyT3R0uA7NRjsbYYSmWRGLgdZunFPJqEFn5fsbhCfD+RXS8yLnm58TxzaL1NTjaJeRjkvp8bnidR3tbLr4mFYpNuO62IUdozMxzDqHiUjqiLKuJo30y8jJSz/C1lo76My3Juju0bgYms9rnqdRHiTV7vYbRZNWaSzPBCmmeZNatklE5Z67pa+mfUyRgoq/8AbZUlj4p2Wf0LOGlzZs2YcF9lOSdFOHB+ebqSzbd8/kjfcP4co7GXDUza4akelGCRjlJlrBwsiyeYRsei4pABABIIABIBABIAABjnSuZAcaTOp0VZYYxvBF0kj40d3s1/+WrwJXDY9EXyAscTu+RWjg4rY9OklsWCGd2o5uZrsTDKxz2No1I5xz8DsJU0zBUwiZRlwKfZdjy7TgqvFXH24ST/AJW0VHxqlq3Z+Ur/AEO9q8KT1S9EVpcBg/dj6IyPRfhetSjhavaCkt2/KMn9jE+0kdoz/py/Q7t9nqf5I+iI/wDHoflXojnwzvyEcFLtH0hV/psldoP/AJ1f+h3q7Pw/KvRHpcCh+VeiHwznyEfPnx5/7VV/8f3IXHJvShU+PKvufRP8jh+VeiPS4LH8q9Ed+GPkHzh8QxMvZpW8Xn9jysJiJ+23bolZH0yPCI9F6IyR4XHoWx0yRB5zgsFwmfQ3+B4c0dLDAJbGeGHSNEcVFUstlDC4M2VOlY9pElyRS3YAB04AAAAAAQCSAAAAACSAAAAAAAACQAQCQAQCQAQCQAQCQAQCQAQCQAQCQAAAAQCQAQCQAQSAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAf//Z', ARRAY['Book authors'], ARRAY['Book tags'], 'Book hash');

-- Belong to user 10 (for search books test)
INSERT INTO "book"("id", "user_id", "library_id", "title", "description", "isbn10", "isbn13", "thumbnail", "authors", "tags", "hash")
  VALUES ('d6f7359c-8f2b-428b-a295-806069e60a3f', 'user10', '4ba98133-ebd1-4fed-b7b2-920745b9c429', 'Le château de ma mère', 'Ce deuxième tome est dans le prolongement chronologique de La Gloire de mon père', 'Book isbn10', 'Book isbn13', '', ARRAY['Marcel Pagnol'], ARRAY['Book tags'], 'Book hash');
INSERT INTO "book"("id", "user_id", "library_id", "title", "description", "isbn10", "isbn13", "thumbnail", "authors", "tags", "hash")
  VALUES ('04d1f1ac-90eb-489c-b39d-71acd572b563', 'user10', '4ba98133-ebd1-4fed-b7b2-920745b9c429', 'Le Ventre de Paris', 'Le personnage principal est Florent, le demi-frère de Quenu', 'Book isbn10', 'Book isbn13', '', ARRAY['Emile Zola'], ARRAY['Book tags'], 'Book hash');
INSERT INTO "book"("id", "user_id", "library_id", "title", "description", "isbn10", "isbn13", "thumbnail", "authors", "tags", "hash")
  VALUES ('8fe9470f-4daf-4559-b903-af9a9937ed72', 'user10', '4ba98133-ebd1-4fed-b7b2-920745b9c429', 'La gloire de ma mère', 'Je suis né dans la ville d''Aubagne, sous le Garlaban couronné de chèvres, au temps des derniers chevriers ', 'Book isbn10', 'Book isbn13', '', ARRAY['Marcel Pagnol'], ARRAY['Book tags'], 'Book hash');
