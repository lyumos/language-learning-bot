CREATE TABLE "tests" (
	"id"	TEXT NOT NULL UNIQUE,
	"word_id"	TEXT NOT NULL,
	"date"	TEXT NOT NULL,
	"status"	TEXT NOT NULL,
	PRIMARY KEY("id"),
	FOREIGN KEY("word_id") REFERENCES "words"("id")
);

CREATE TABLE "words" (
	"id"	TEXT NOT NULL UNIQUE,
	"word"	TEXT NOT NULL,
	"category" TEXT NOT NULL,
	"status"	TEXT NOT NULL,
	PRIMARY KEY("id")
);