CREATE TABLE b50Custom(
    QQ      TEXT,
    plateId TEXT,
    frameId TEXT
);

CREATE TABLE plateIdList(
    plateId TEXT
);

CREATE TABLE frameIdList(
    frameId TEXT
);

CREATE TABLE poke(
    QQ          TEXT,
    pokeCount   INTEGER
);

CREATE TABLE eatMeal(
    QQ          TEXT,
    eatCount    INTEGER
);

INSERT INTO b50Custom VALUES('default', '200101', '259505');
INSERT INTO b50Custom VALUES('1179782321', '206201', '259505')