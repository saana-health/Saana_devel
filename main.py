from saana_lib import optimizeMeal
import sys

if len(sys.argv) > 1 and sys.argv[1] == 'test':
    print('Running TEST mode')
    op = optimizeMeal.Optimizer(True)
    op.optimize()
elif len(sys.argv) > 1 and sys.argv[1] == 'prod':
    print('Running PRODUCTION mode')
    op = optimizeMeal.Optimizer(False)
    op.optimize()
elif len(sys.argv) == 1:
    print('Needs an argument: ["test"/"prod"]')
else:
    print('Invalid argument {}: choose between "test" and "prod"'.format(sys.argv[1]))
