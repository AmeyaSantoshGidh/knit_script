from typing import Optional


class Knitout_Line:
    """
        General class for lines of knitout
    """

    def __init__(self, comment: Optional[str]):
        self.comment = comment

    @property
    def has_comment(self) -> bool:
        """
        :return: True if comment is present
        """
        return self.comment is not None

    @property
    def comment_str(self) -> str:
        """
        :return: comment as a string
        """
        if not self.has_comment:
            return "\n"
        else:
            return f";{self.comment}\n"

    def __str__(self):
        return self.comment_str

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        return str(self) == str(other)


class Version_Line(Knitout_Line):

    def __init__(self, version: int, comment: Optional[str]=None):
        super().__init__(comment)
        self.version = version

    def __str__(self):
        return f";!knitout-{self.version}{self.comment_str}"


class Comment_Line(Knitout_Line):
    def __init__(self, comment: Optional[str]):
        super().__init__(comment)