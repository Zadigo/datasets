import pandas
from functools import lru_cache


@lru_cache(maxsize=100)
def main():
    df = pandas.read_csv('tmp/fix_missed_producers.csv')
    
    while True:
        linenumber = input('Enter line number: ')
        value = input('Enter value: ')

        if value.lower() == 'exit':
            break

        if ', artist' in value:
            value = value.replace(', artist', ' > artist')

        if ', conductor' in value:
            value = value.replace(', conductor', ' > conductor')

        if ', songwriter' in value:
            value = value.replace(', songwriter', ' > songwriter')

        if ', pianist' in value:
            value = value.replace(', pianist', ' > pianist')

        if ', composer' in value:
            value = value.replace(', composer', ' > composer')

        if ', arranger' in value:
            value = value.replace(', arranger', ' > arranger')

        if ', engineer/mixer' in value:
            value = value.replace(', engineer/mixer', ' > engineer/mixer')

        if ', producer' in value:
            value = value.replace(', producer', ' > producer')

        value = value.replace(',', ';')

        if linenumber != '':
            linenumber = int(linenumber)

        print('Processed value:', value, '\n\n')


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt as e:
        print('\nExiting program.')
