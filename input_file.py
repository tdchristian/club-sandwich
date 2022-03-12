from __future__ import annotations

class InputFile:
    """
    Represents an input file specification.
    """
    __slots__ = ('filename', 'source', 'notes', 'columns')

    filename: str
    source: str
    notes: str
    columns: list[InputFileColumn]
    
    def __init__(self: InputFile, filename: str, source: str, notes: str) -> None:
        """
        Initialize this input file with the given data. Columns begin blank.
        """
        
        self.filename = filename
        self.source = source
        self.notes = notes
        self.columns = []

    def add_column(self: InputFile, column: InputFileColumn) -> None:
        """
        Add the given column to this input file.
        """
        self.columns.append(column)

    def __repr__(self: InputFile) -> str:
        """
        Return a string representation of this input file (its filename).
        """
        return self.filename

class InputFileColumn:
    """
    Represents a column in an input file.
    """
    __slots__ = ('name', 'datatype', 'example', 'default', 'notes')

    name: str
    datatype: str
    example: str
    default: str
    notes: str

    def __init__(self: InputFileColumn, name: str, datatype: str, example: str, default: str, notes: str) -> None:
        """
        Initialize this input file column with the given data.
        """

        self.name = name
        self.datatype = datatype
        self.example = example
        self.default = default
        self.notes = notes

    def __repr__(self: InputFileColumn) -> str:
        """Return a string representation of this column (its name)."""
        return self.name
