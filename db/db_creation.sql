CREATE TABLE "words" (
	"id"	TEXT NOT NULL UNIQUE,
	"word"	TEXT NOT NULL,
	"category" TEXT NOT NULL,
	"status"	TEXT NOT NULL,
	"modified_date" TEXT NOT NULL,
	"user_id" TEXT NOT NULL,
	PRIMARY KEY("id")
);
CREATE TABLE "settings" (
    "user_id" TEXT NOT NULL UNIQUE,
    "daily_message_enabled" TEXT NOT NULL,
    "review_message_enabled" TEXT NOT NULL,
    PRIMARY KEY("user_id")
);