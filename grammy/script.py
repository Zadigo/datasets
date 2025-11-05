import pandas
import pathlib
from functools import lru_cache


BASE_DIR = pathlib.Path(__file__).parent.absolute()


@lru_cache(maxsize=100)
def main():
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

        if ', composer & lyricist' in value:
            value = value.replace(', composer & lyricist',
                                  ' > composer & lyricist')

        if ', lyricist' in value:
            value = value.replace(', lyricist', ' > lyricist')

        if ', principal vocalists' in value:
            value = value.replace(', principal vocalists',
                                  ' > principal vocalists')

        if ', art directors' in value:
            value = value.replace(', art directors', ' > art directors')

        if ', album notes writers' in value:
            value = value.replace(', album notes writers',
                                  ' > album notes writers')

        if ', engineers' in value:
            value = value.replace(', engineers', ' > engineers')

        if ', engineer' in value:
            value = value.replace(', engineer', ' > engineer')

        if ', mastering engineer' in value:
            value = value.replace(', mastering engineer',
                                  ' > mastering engineer')

        if ', remixers' in value:
            value = value.replace(', remixers', ' > remixers')

        if ',  immersive' in value:
            value = value.replace(',  immersive', ' > immersive')

        if ', compilation producer' in value:
            value = value.replace(', compilation producer',
                                  ' > compilation producer')

        if ',  restoration engineer' in value:
            value = value.replace(',  restoration engineer',
                                  ' > restoration engineer')

        value = value.replace(',', ';')

        if linenumber != '':
            linenumber = int(linenumber)

            if value != '':
                df = pandas.read_csv(BASE_DIR / 'tmp/fixes.csv')

                if linenumber in df.line.values:
                    continue

                s = pandas.Series([linenumber, value], index=[
                                  'line', 'producers'])
                df = pandas.concat([df, s.to_frame().T], ignore_index=True)

                df.to_csv(BASE_DIR / 'tmp/fixes.csv', index=False)
                print('Processed value:', value, '\n\n')


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt as e:
        print('\nExiting program.')
