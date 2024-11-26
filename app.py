# app.py
from flask import Flask, render_template, request, jsonify
import ast
import operator
import re
import ply.lex as lex

app = Flask(__name__)

tokens = (
    'NUMBER',  # Para los números
    'PLUS',    # Para el operador +
    'MINUS',   # Para el operador -
    'TIMES',   # Para el operador *
    'DIVIDE',  # Para el operador /
    'LPAREN',  # Para el paréntesis (
    'RPAREN',  # Para el paréntesis )
)

# Expresiones regulares para cada tipo de token
t_PLUS = r'\+'
t_MINUS = r'-'
t_TIMES = r'\*'
t_DIVIDE = r'/'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_NUMBER = r'\d+'  # Para números (solo enteros)

# Regla de manejo de saltos de línea y espacios en blanco (no necesarios en el análisis)
t_ignore = ' \t\n'

# Construimos el lexer
lexer = lex.lex()

# Función para analizar una expresión
def tokenize_expression(expression):
    lexer.input(expression)
    tokens = []
    while True:
        tok = lexer.token()
        if not tok:
            break
        tokens.append(tok)
    return tokens

class TokenAnalyzer:
    def analyze_tokens(self, expression):
        tokens = []
        summary = {
            'total_enteros': 0,
            'total_operadores': 0,
            'total_puntos_decimales': 0,
            'total_partes_decimales': 0
        }
        
        # Patrón para identificar números, operadores y paréntesis
        pattern = r'(\d*\.\d+|\d+|[-+*/()])'
        raw_tokens = re.findall(pattern, expression)
        
        for token in raw_tokens:
            if '.' in token:  # Número flotante
                parts = token.split('.')
                tokens.extend([
                    {'token': parts[0], 'tipo': 'Parte entera'},
                    {'token': '.', 'tipo': 'Punto decimal'},
                    {'token': parts[1], 'tipo': 'Parte decimal'}
                ])
                summary['total_enteros'] += 1
                summary['total_puntos_decimales'] += 1
                summary['total_partes_decimales'] += 1
            elif token.isdigit():  # Número entero
                tokens.append({'token': token, 'tipo': 'Número entero'})
                summary['total_enteros'] += 1
            elif token in '+-*/':  # Operadores
                tipo_op = {
                    '+': 'Operador suma',
                    '-': 'Operador resta',
                    '*': 'Operador multiplicación',
                    '/': 'Operador división'
                }
                tokens.append({'token': token, 'tipo': tipo_op[token]})
                summary['total_operadores'] += 1
            elif token in '()':  # Paréntesis
                tipo_par = {
                    '(': 'Paréntesis izquierdo',
                    ')': 'Paréntesis derecho'
                }
                tokens.append({'token': token, 'tipo': tipo_par[token]})
        
        return tokens, summary


class ExpressionTreeBuilder:
    def __init__(self):
        self.operators = {
            ast.Add: '+',
            ast.Sub: '-',
            ast.Mult: '*',
            ast.Div: '/',
        }
    
    def build_tree(self, expr_str):
        try:
            tree = ast.parse(expr_str, mode='eval')
            return self._process_node(tree.body)
        except:
            return {"error": "Invalid expression"}
    
    def _process_node(self, node):
        if isinstance(node, ast.Num):
            return {
                "name": str(node.n),
                "children": []
            }
        elif isinstance(node, ast.BinOp):
            return {
                "name": self.operators.get(type(node.op), '?'),
                "children": [
                    self._process_node(node.left),
                    self._process_node(node.right)
                ]
            }
        return {"name": "?", "children": []}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    data = request.get_json()
    expression = data.get('expression', '')
    
    try:
        # Analizar tokens
        token_analyzer = TokenAnalyzer()
        tokens, summary = token_analyzer.analyze_tokens(expression)
        
        # Calcular el resultado
        result = eval(expression)
        
        # Construir el árbol
        tree_builder = ExpressionTreeBuilder()
        tree = tree_builder.build_tree(expression)
        
        return jsonify({
            'result': result,
            'tree': tree,
            'tokens': tokens,
            'summary': summary
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

    
if __name__ == '__main__':
    app.run(debug=True)