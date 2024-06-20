CREATE TABLE "examples" (
	"id"	TEXT NOT NULL UNIQUE,
	"word_id"	TEXT NOT NULL,
	"example"	TEXT NOT NULL,
	"translation"	TEXT NOT NULL,
	PRIMARY KEY("id"),
	FOREIGN KEY("word_id") REFERENCES "words"("id")
);

CREATE TABLE "definitions" (
	"id"	TEXT NOT NULL UNIQUE,
	"word_id"	TEXT NOT NULL,
	"definitions"	TEXT NOT NULL,
	"language"	TEXT NOT NULL,
	PRIMARY KEY("id"),
	FOREIGN KEY("word_id") REFERENCES "words"("id")
);

CREATE TABLE "tests" (
	"id"	TEXT NOT NULL UNIQUE,
	"word_id"	TEXT NOT NULL,
	"date"	TEXT NOT NULL,
	"status"	TEXT NOT NULL,
	FOREIGN KEY("word_id") REFERENCES "words"("id")
);

CREATE TABLE "words" (
	"id"	TEXT NOT NULL UNIQUE,
	"word"	TEXT NOT NULL,
	"translation" TEXT,
	"synonyms" TEXT,
	"antonyms" TEXT,
	"status"	TEXT NOT NULL,
	PRIMARY KEY("id")
);