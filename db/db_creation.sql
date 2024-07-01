CREATE TABLE "words" (
	"id"	TEXT NOT NULL UNIQUE,
	"word"	TEXT NOT NULL,
	"category" TEXT NOT NULL,
	"status"	TEXT NOT NULL,
	PRIMARY KEY("id")
);