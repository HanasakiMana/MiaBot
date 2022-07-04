CREATE TABLE musicInfo(
    id          TEXT
    title       TEXT
    artist      TEXT
    genre       TEXT
    bpm         INTEGER
    addVersion  TEXT
    stdChartId  TEXT
    dxChartId   TEXT
    isNew       INTEGER
)

CREATE TABLE chartInfo(
    chartId TEXT
    diffLevel INTEGER
    chartLevel TEXT
    chartDs REAL
    charter TEXT
    noteTap INTEGER
    noteHold INTEGER
    noteSlide INTEGER
    noteTouch INTEGER
    noteBreak INTEGER
)
