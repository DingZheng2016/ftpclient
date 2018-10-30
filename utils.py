
def readable(text):
    if text.startswith('1') or text.startswith('2') or text.startswith('3'):
        return colorful(text, 'green')
    else:
        return colorful(text, 'red')

def colorful(text, color):
    return '<span style="color:%s;">' % color + text + '</span>'
