try:
    import mkcmdlinegame
except ImportError:
    sys.path.append(
        join(dirname(dirname(realpath(__file__))), 'lib', 'python3')
    )
    import mkcmdlinegame
