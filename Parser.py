import sys
import re
from collections import OrderedDict
#returning true represents that whatever function or statement of code is valid syntax or lexically valid unless otherwise noted
#returning false represents that whatever function or statement of code is invalid syntax or lexically invalid unless otherwise noted
#true being passed as a parameter represents some function being optional in the syntax, like the sign before a term in the expression definition.
#the ignore_errors variable is passed as a parameter when something is required in the grammer, like the read keyword in the read statement.
class LexAnalyzer:
	#initialization of the ordered dictionary
	od = OrderedDict({'WHITE_SPACE':'^[ \t]+', 'NEW_LINE':'^\n', 'prog':'^prog', 'begin':'^begin', 'end':'^end', 'read':'^read', 'write':'^write', 'if':'^if', 'then':'^then', 'else':'^else', 'do':'^do', 'while':'^while', 'ARROW':'^<-', 'COMMA':'^,', 'SEMICOLON':'^;', 'LPAREN':'^[(]', 'RPAREN':'^[)]', 'ADD_OP':'^[+]', 'SUB_OP':'^[-]', 'MULT_OP':'^[*]', 'DIV_OP':'^[/]', 'EQUAL':'^=', 'INEQ':'^<>', 'LTHAN':'^<', 'LEQUAL':'^<=', 'GEQUAL':'^>=','GTHAN':'^>', 'COMMENT':'\/\/.*\\n', 'PROG_NAME':'^[A-Z]([A-Za-z]|[0-9])*', 'VAR':'^[A-Za-z]([A-Za-z]|[0-9])*', 'INT_LIT':'^([0-9])*',})
	#list of keywords to differentiate between variable names and tokens
	keywords = ['prog', 'begin', 'end', 'read', 'write', 'if', 'then', 'else', 'do', 'while']
	#miscellaneous variable initialization
	token = ""
	lexeme = ""
	contents = ""
	line = 1
	#constructor for LexAnalzyer Class that allows the file inputted from the command line to be opened for reading
	def __init__(self, file_name):
		with open (file_name, "r") as file:
			self.contents = file.read()

	#lex function that matches token and lexeme pairs.
	def lex(self, key, ignore_errors):
		while 1:
			#if the length of the file we are reading is 0, we set the token and lexeme to "EOF" token and return that we are at the end of the file.
			if len(self.contents) == 0:
				self.token = "EOF"
				self.lexeme = "EOF"
				return key == "EOF"
			#if we still need to read the file, we get the value of the ordered dictionary we are trying to match and match it using a RegEx function
			temp_val = self.od[key]
			match = re.search(temp_val, self.contents)
			temp_lexeme = ""
			#if there is a match, we get the token and lexeme
			if match:
				temp_token = key
				temp_lexeme = match.group()
				# consider the case where a keyword like 'begin' may match as a var or progname
				if temp_lexeme in self.keywords and (key == "VAR" or key == "PROG_NAME"):
					if not ignore_errors:
						print("Syntax Error: Variable name cannot be a keyword")
						print("Trying again...")
						self.contents = self.contents[len(temp_lexeme):]
						self.strip_contents()
						continue
					else:
						return False
				#if the lexeme is a comment you cut whatever follows the comment token out of the contents file.
				elif temp_lexeme in self.od and (key == "COMMENT"):
					self.contents = self.contents.split(' \n')
					self.strip_contents()
				#otherwise, the token and lexeme are set and the pair is removed from the contents file.
				else:
					self.token = temp_token
					self.lexeme = temp_lexeme
					self.contents = self.contents[len(temp_lexeme):]
					self.strip_contents()
					return True
			#otherwise, you get the temporary lexeme again and account for syntax errors
			else:
				temp_lexeme = self.contents.split()[0]
				if not ignore_errors:
					print("Syntax Error; Expected:", key, "but got:", temp_lexeme, "on line:", self.line)
					print("Trying again...")
					self.contents = self.contents[len(temp_lexeme):]
					self.strip_contents()
					continue
				else:
					return False

	#strips white space while keeping track of line number
	def strip_contents(self):
		while 1:
			self.contents = self.contents.strip(' \t')
			#print(self.contents)
			if len(self.contents) > 0 and self.contents[0] == '\n':
				self.line = self.line + 1
				self.contents = self.contents[1:]
			else:
				return

class SyntaxAnalyzer:
	lexer = None

	#constructor for SyntaxAnalyzer Class, creates a lexical analyzer instance
	def __init__(self, file_name):
		self.lexer = LexAnalyzer(file_name)

	# terminal function parses terminals listed in the ordered dictionary
	def terminal(self, key, ignore_errors = False):
		return self.lexer.lex(key, ignore_errors)

	#program subroutine. checks if there is a prog keyword and if there is a valid prog_name as well.
	def program(self):
		success = self.terminal("prog")
		if not success:
			return False

		success = self.prog_name()
		if not success:
			return False
		success = self.comp_stmt()
		#if a compound statement is not found, then you check if it is the end of the file.
		if not success:
			return False
		success = self.terminal("EOF")
		if not success:
			return False
		#otherwise return that it is a valid program statement
		return True

	#compound statement subroutine. checks if there are begin and end keywords
	def comp_stmt(self, ignore_errors = False):
		success = self.terminal("begin", ignore_errors)
		if not success:
			return False
		#calls statement list subroutine to account for if the comp stmt has one or multiple statments if at all. returns false if there is not at least one statement found.
		success = self.stmt_list(ignore_errors)
		if not success:
			return False
		success = self.terminal("end", ignore_errors)
		if not success:
			return False
		#returns that it is a valid comp stmt if all criterium is met.
		return True

	#stmt list subroutine that checks if there is one or multiple statements within something else.
	#stmt list method added for ease of checking for one or multiple statements.
	def stmt_list(self, ignore_errors = False):
		success = self.stmt(ignore_errors)
		#if at least one statement was not found, then it is not a valid statement list.
		if not success:
			return False
		#if one statement is found and the next token is a semicolon followed by another statement, then it is a valid statment list.
		success = self.terminal("SEMICOLON", True)
		if not success:
			return True
		success = self.stmt_list(ignore_errors)
		return success

	#statement subroutine. checks if a statement is either a simple or structured statemetn and if it is either of them, returns true.
	def stmt(self, ignore_errors = False):
		success = self.simp_stmt(True)
		if success:
			return True
		success = self.struct_stmt(ignore_errors)
		if success:
			return True
		return False

	#checks if a statement is a simple statement by checking if it is an assign, read or write statement.
	#if it is one of the three options, returns true, otherwise false.
	def simp_stmt(self, ignore_errors = False):
		success = self.assign_stmt(True)
		if success:
			return True
		success = self.read_stmt(True)
		if success:
			return True
		success = self.write_stmt(ignore_errors)
		if success:
			return True
		return False

	#checks if there is a valid assignment statement. must have an arrow terminal as well as a variable on the LHS and expr on the RHS. returns false if invalid.
	def assign_stmt(self, ignore_errors = False):
		success = self.var(ignore_errors)
		if not success:
			return False
		success = self.terminal("ARROW", ignore_errors)
		if not success:
			return False
		success = self.expr(ignore_errors)
		return True

	#checks for valid read statements. must find a read keyword and open and closing parenthesis surrounding some sort of variable list.
	def read_stmt(self, ignore_errors = False):
		success = self.terminal("read", ignore_errors)
		if not success:
			return False
		success = self.terminal("LPAREN", ignore_errors)
		if not success:
			return False
		success = self.var_list(ignore_errors)
		success = self.terminal("RPAREN", ignore_errors)
		if not success:
			return False
		return True

	#checks for valid write statement. must find a write keyword and open/closing parens surrounding some sort of expr list.
	def write_stmt(self, ignore_errors = False):
		success = self.terminal("write", ignore_errors)
		if not success:
			return False
		success = self.terminal("LPAREN", ignore_errors)
		if not success:
			return False
		success = self.expr_list(ignore_errors)
		success = self.terminal("RPAREN", ignore_errors)
		if not success:
			return False
		return True

	#structured statement subroutine. checks if there is a compound statement or if or while statement. if one returns true, then it is a valid structured statement. otherwise is false.
	def struct_stmt(self, ignore_errors = False):
		success = self.comp_stmt(True)
		if success:
			return True
		success = self.if_stmt(True)
		if success:
			return True
		success = self.while_stmt(ignore_errors)
		if success:
			return True
		return False

	#if statemetn subroutine. checks for if, then and optional else keywords. as long as if and then are included in between statements, it is a valid if statement. if else is included there must be a statement following.
	def if_stmt(self, ignore_errors = False):
		success = self.terminal("if", ignore_errors)
		if not success:
			return False
		success = self.expr(ignore_errors)
		success = self.terminal("then", ignore_errors)
		if not success:
			return False
		success = self.stmt(ignore_errors)
		success = self.terminal("else", True)
		if not success:
			return True
		success = self.stmt(ignore_errors)
		return True

	#while statement subroutine. checks for while keyword followed by an expr and do keyword followed by a statement.
	def while_stmt(self, ignore_errors = False):
		success = self.terminal("while", ignore_errors)
		if not success:
			return False
		success = self.expr(ignore_errors)
		success = self.terminal("do", ignore_errors)
		if not success:
			return False
		success = self.stmt()
		return True

	#expr list subroutine to account for one or multiple exprs being present
	#expr list was written for the convenience of checking for one or multiple exprs.
	#if a comma is found following an expr there must be another expr afterwards for it to be valid syntax
	def expr_list(self, ignore_errors = False):
		success = self.expr(ignore_errors)
		success = self.terminal("COMMA", True)
		if not success:
			return True
		success = self.expr(ignore_errors)
		return True

	#expr subroutine, checks if it is a simple expression or if it is a simp expr followed by both a relational op and another simp expr.
	def expr(self, ignore_errors = False):
		success = self.simp_expr(ignore_errors)
		success = self.relat_ops(True)
		if not success:
			return True
		success = self.simp_expr(ignore_errors)
		return success

	#simple expression subroutine. checks if the syntax has the optional sign, and then if there is a term, or if there is the optional sign, term then add op and another term.
	def simp_expr(self, ignore_errors = False):
		success = self.sign(True)
		success = self.term(ignore_errors)
		success = self.add_op(True)
		if not success:
			return True
		success = self.term(ignore_errors)
		return success

	#term subroutine. checks for a factor or a factor followed by a mult op then another factor.
	def term(self, ignore_errors = False):
		success = self.factor(ignore_errors)
		success = self.mult_op(True)
		if not success:
			return True
		success = self.factor(ignore_errors)
		return success

	#factor subroutine. checks for either a variable, int literal, or expression in parenthesis. any of the three are valid factors.
	def factor(self, ignore_errors = False):
		success = self.var(True)
		if success:
			return True
		success = self.terminal("INT_LIT", True)
		if success:
			return True
		success = self.terminal("LPAREN", ignore_errors)
		if not success:
			return False
		success = self.expr(ignore_errors)
		success = self.terminal("RPAREN", ignore_errors)
		if not success:
			return False
		return True

	#sign subroutine. checks if there is either and add or sub op present in the syntax.
	def sign(self, ignore_errors = False):
		success = self.terminal("ADD_OP", True)
		if success:
			return True
		success = self.terminal("SUB_OP", ignore_errors)
		if success:
			return True
		return False

	#add op function that checks if there is a sign present since a sign is +/- and an add_op is also +/-
	def add_op(self, ignore_errors = False):
		return self.sign(ignore_errors)

	#mult op function that checks if a * or / is present in the syntax
	def mult_op(self, ignore_errors = False):
		success = self.terminal("MULT_OP", True)
		if success:
			return True
		success = self.terminal("DIV_OP", ignore_errors)
		if success:
			return True
		return False

	#relational ops function that checks if one of the following is present in the syntax: <, >, <=, >=, =
	def relat_ops(self, ignore_errors = False):
		success = self.terminal("EQUAL", True)
		if success:
			return True
		success = self.terminal("INEQ", True)
		if success:
			return True
		success = self.terminal("LTHAN", True)
		if success:
			return True
		success = self.terminal("LEQUAL", True)
		if success:
			return True
		success = self.terminal("GEQUAL", True)
		if success:
			return True
		success = self.terminal("GTHAN", ignore_errors)
		if success:
			return True
		return False

	#variable list subroutine to check if there is one or more variables
	#written for the convenience of checking for valid variable lists in other functions.
	#if there is a comma following a variable then we check if there is anothe variable after the comma.
	def var_list(self, ignore_errors = False):
		success = self.var(ignore_errors)
		success = self.terminal("COMMA", True)
		if not success:
			return True
		sucess = self.var(ignore_errors)
		return success

	#variable function that calls the terminal method to check if there is a "VAR" token
	def var(self, ignore_errors = False):
		return self.terminal("VAR", ignore_errors)

	#int lit function that calls the terminal method to check if there is a "INT_LIT" token
	def int_literal(self, ignore_errors = False):
		return self.terminal("INT_LIT", ignore_errors)

	#prog_name function that calls the terminal method to check if there is a "PROG_NAME" token
	def prog_name(self, ignore_errors = False):
		return self.terminal("PROG_NAME", ignore_errors)

	#parse method that calls the program method to start parsing the file that the user inputs.
	def parse(self, ignore_errors = False):
		return self.program()

	#comment method that calls the terminal method to check for "COMMENT" token
	def comment(self, ignore_errors = False):
		return self.terminal("COMMENT", ignore_errors)

#creates a syntax analyzer object to accept a file name from the command line
syntax = SyntaxAnalyzer(sys.argv[1])
#commented out following line because it prints true or false depending on if a program is syntactically and lexically valid
#print(syntax.parse())
