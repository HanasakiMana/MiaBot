CREATE TABLE musicInfo(
    id              TEXT,
    title           TEXT,
    artist          TEXT,
    genre           TEXT,
    bpm             INTEGER,
    addVersion      TEXT,
    isNew           INTEGER,
    stdChartId      TEXT,
    dxChartId       TEXT
);

CREATE TABLE chartInfo(
    chartId             TEXT,
    chartType           TEXT,
    musicId             TEXT,
    
    basicLevel          TEXT,
    basicDs             REAL,
    basicCharter        TEXT,
    basicTap            INTEGER,
    basicHold           INTEGER,
    basicSlide          INTEGER,
    basicTouch          INTEGER,
    basicBreak          INTEGER,
    
    advancedLevel       TEXT,
    advancedDs          REAL,
    advancedCharter     TEXT,
    advancedTap         INTEGER,
    advancedHold        INTEGER,
    advancedSlide       INTEGER,
    advancedTouch       INTEGER,
    advancedBreak       INTEGER,
    
    expertLevel         TEXT,
    expertDs            REAL,
    expertCharter       TEXT,
    expertTap           INTEGER,
    expertHold          INTEGER,
    expertSlide         INTEGER,
    expertTouch         INTEGER,
    expertBreak         INTEGER,
    
    masterLevel         TEXT,
    masterDs            REAL,
    masterCharter       TEXT,
    masterTap           INTEGER,
    masterHold          INTEGER,
    masterSlide         INTEGER,
    masterTouch         INTEGER,
    masterBreak         INTEGER,
    
    remLevel            TEXT,
    remDs               REAL,
    remCharter          TEXT,
    remTap              INTEGER,
    remHold             INTEGER,
    remSlide            INTEGER,
    remTouch            INTEGER,
    remBreak            INTEGER
);

CREATE TABLE dbInfo(
    updateTime  TEXT
)