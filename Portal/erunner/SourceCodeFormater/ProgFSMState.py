# -*- encoding: utf-8 -*-
__author__ = 'Wang Shuhao'


from .Error import TargetSourceEOF
from .FSMState import SourceParseFSMState


class SourceParseFSMNormalState(SourceParseFSMState):
    def input(self):
        while True:
            try:
                readchar = self.inputCtx.input()
                if readchar in self.syntax["conflict"]:
                    self.inputCtx.uninput()
                    self.setState(SourceParseFSMConflict(self.context, self.inputCtx, self.syntax))
                    return "ident", self.inputCtx.getInputBuf()
                elif readchar in self.syntax["separator"]:
                    self.inputCtx.uninput()
                    self.setState(SourceParseFSMSeparatorState(self.context, self.inputCtx, self.syntax))
                    return "ident", self.inputCtx.getInputBuf()
                elif readchar in self.syntax["operator"]:
                    self.inputCtx.uninput()
                    self.setState(SourceParseFSMOperatorState(self.context, self.inputCtx, self.syntax))
                    return "ident", self.inputCtx.getInputBuf()
                elif readchar in self.syntax["string"]:
                    self.inputCtx.uninput()
                    self.setState(SourceParseFSMStringState(self.context, self.inputCtx, self.syntax))
                    return "ident", self.inputCtx.getInputBuf()
                elif readchar == "\n" or readchar == "\r":
                    self.inputCtx.uninput()
                    self.setState(SourceParseFSMEOLState(self.context, self.inputCtx, self.syntax, self))
                    return "ident", self.inputCtx.getInputBuf()
                elif readchar in self.syntax["comment"]:
                    self.inputCtx.uninput()
                    self.setState(SourceParseFSMCommentState(self.context, self.inputCtx, self.syntax))
                    return "ident", self.inputCtx.getInputBuf()
            except TargetSourceEOF as e:
                e.params = ("ident", self.inputCtx.getInputBuf())
                raise e


class SourceParseFSMSeparatorState(SourceParseFSMState):
    def input(self):
        while True:
            try:
                readchar = self.inputCtx.input()
                if readchar not in self.syntax["separator"]:
                    self.inputCtx.uninput()
                    self.setState(SourceParseFSMNormalState(self.context, self.inputCtx, self.syntax))
                    return "separator", self.inputCtx.getInputBuf()
            except TargetSourceEOF as e:
                e.params = ("separator", self.inputCtx.getInputBuf())
                raise e


class SourceParseFSMBlankState(SourceParseFSMState):
    def input(self):
        while True:
            try:
                readchar = self.inputCtx.input()
                if readchar != ' 'or readchar != '\t':
                    self.inputCtx.uninput()
                    self.setState(SourceParseFSMSeparatorState(self.context, self.inputCtx, self.syntax))
                    return "blank", self.inputCtx.getInputBuf()
            except TargetSourceEOF as e:
                e.params = ("blank", self.inputCtx.getInputBuf())
                raise e


class SourceParseFSMStringState(SourceParseFSMState):
    def input(self):
        readchar = self.inputCtx.input()
        if readchar in self.syntax["string"]:
            self.setState(SourceParseFSMStringLineState(self.context, self.inputCtx, self.syntax, readchar))
            return None, None


class SourceParseFSMStringLineState(SourceParseFSMState):
    def input(self):
        endOfString = self.args[0]

        escape = False
        while True:
            try:
                readchar = self.inputCtx.input()

                if readchar == "\\":
                    escape = not escape
                elif readchar == endOfString:
                    if escape:
                        escape = not escape
                    else:
                        self.setState(SourceParseFSMNormalState(self.context, self.inputCtx, self.syntax))
                        return "string", self.inputCtx.getInputBuf()
                else:
                    if escape:
                        escape = not escape
            except TargetSourceEOF as e:
                e.params = ("string", self.inputCtx.getInputBuf())
                raise e


class SourceParseFSMOperatorState(SourceParseFSMState):
    def input(self):
        self.inputCtx.input()
        self.setState(SourceParseFSMNormalState(self.context, self.inputCtx, self.syntax))
        return "operator", self.inputCtx.getInputBuf()


class SourceParseFSMCommentState(SourceParseFSMState):
    def input(self):
        while True:
            try:
                readchar = self.inputCtx.input()
                if readchar == "\r" or readchar == "\n":
                    self.inputCtx.uninput()
                    self.setState(SourceParseFSMEOLState(self.context, self.inputCtx, self.syntax))
                    return "comment", self.inputCtx.getInputBuf()
            except TargetSourceEOF as e:
                e.params = ("comment", self.inputCtx.getInputBuf())
                raise e


class SourceParseFSMEOLState(SourceParseFSMState):
    def input(self):
        """
            self.args[0]  -->  prevState
        """
        char = self.inputCtx.input()
        if char == "\n":
            self.setState(SourceParseFSMNormalState(self.context, self.inputCtx, self.syntax))
            return "crlf", self.inputCtx.getInputBuf()
        char = self.inputCtx.input()
        if char == "\r":
            char = self.inputCtx.input()
            if char != "\n":
                self.inputCtx.uninput()
            self.setState(SourceParseFSMNormalState(self.context, self.inputCtx, self.syntax))
            return "crlf", self.inputCtx.getInputBuf()


__STATE_MAP__ = {
    "normal": SourceParseFSMNormalState,
    "comment": SourceParseFSMCommentState,
    "operator": SourceParseFSMOperatorState,
    "separator": SourceParseFSMSeparatorState,
    "string": SourceParseFSMStringState
}


class SourceParseFSMConflict(SourceParseFSMState):
    def input(self):
        global __STATE_MAP__
        """
            self.args[0] --> readchar
        """

        nextChar = self.inputCtx.input()
        conflict = self.syntax["conflict"][nextChar]
        if nextChar == conflict["expect"]:
            state = conflict["expect_state"]
            self.setState(__STATE_MAP__[state](self.context, self.inputCtx, self.syntax))
            return None, None
        else:
            state = conflict["unexpect_state"]
            self.setState(__STATE_MAP__[state](self.context, self.inputCtx, self.syntax))
            return None, None

