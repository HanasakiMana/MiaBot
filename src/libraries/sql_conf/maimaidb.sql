CREATE TABLE musicInfo(
    id              TEXT,
    title           TEXT,
    artist          TEXT,
    genre           TEXT,
    bpm             INTEGER,
    addVersion      TEXT,
    stdChartId      TEXT,
    stdCartLevel    TEXT,
    dxChartId       TEXT,
    dxChartLevel    TEXT,
    isNew           INTEGER
);

CREATE TABLE chartInfo(
    chartId     TEXT,
    musicId     TEXT,
    diffLevel   INTEGER,
    chartLevel  TEXT,
    chartDs     REAL,
    charter     TEXT,
    noteTap     INTEGER,
    noteHold    INTEGER,
    noteSlide   INTEGER,
    noteTouch   INTEGER,
    noteBreak   INTEGER
);

CREATE TABLE dbInfo(
    updateTime TEXT
)