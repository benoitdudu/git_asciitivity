
import subprocess
import datetime
import os
import pixel_art
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--start_date',
                    type=lambda d: datetime.datetime.strptime(d, '%Y-%m-%d').date(),
                    help='Set the starting date (in format Year-Month-Day)', required=True)
parser.add_argument('--end_date',
                    type=lambda d: datetime.datetime.strptime(d, '%Y-%m-%d').date(),
                    help='Set the ending date (in format Year-Month-Day)', required=True)
parser.add_argument('--text',
                    type=str,
                    help='the ascii text to convert in "git commit"', required=True)
parser.add_argument('--nb_commit_background',
                    type=int,
                    help='the number of "git commit" to create the background', default = 0)
parser.add_argument('--nb_commit_foreground',
                    type=int,
                    help='the number of "git commit" to create the foreground', default = 10)
args = parser.parse_args()

print(args.start_date)
print(args.end_date)
print(args.text)

# p = pixel_art.PixelArt(args.text)
# p.write_pixels_to_file('result.txt')


def create_date_matrix(startDate, endDate):
    matrix = [[None], [None], [None], [None], [None], [None], [None]]
    # in Date class Monday is 0 and Sunday 6
    # remapDay is used to map Sunday to 0, Monday to 1 and so on
    remapDay = {0: 1, 1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 0}
    weekNumber = 0
    delta = datetime.timedelta(days=1)

    currentDate = startDate
    while currentDate <= endDate:
        if weekNumber == 0:
            matrix[remapDay[currentDate.weekday()]] = [currentDate]
        else:
            matrix[remapDay[currentDate.weekday()]].append(currentDate)

        currentDate += delta
        if (currentDate.weekday() == 6) and (currentDate != startDate):
            # update week number after second sunday
            weekNumber += 1
    while currentDate.weekday() != 6:
        matrix[remapDay[currentDate.weekday()]].append(None)
        currentDate += delta
    return matrix

def check_text_and_date_fit(dateMatrix, pixelMatrix):
    if len(dateMatrix) != len(pixelMatrix):
        print(f'dates ({len(dateMatrix)} rows) and pixels ({len(pixelMatrix)} rows) do not have the same number of rows...')
        exit(1)
    isTextTrucated = False
    for i in range(0, len(dateMatrix)):
        if len(dateMatrix[i]) < len(pixelMatrix[i]):
            isTextTrucated = True
    if isTextTrucated:
        print('The numbers of dates is lower than the text length... the text will be truncated')

class CommitMatrixElm:
    def __init__(self, date: datetime, nb_commit: int) -> None:
        self.date = date
        self.nb_commit = nb_commit
        pass

class CommitMatrix:
    def __init__(self, start_date: datetime, end_date: datetime,
                 text: str, nb_commit_background: int, nb_commit_foreground: int) -> None:
        self._date_matrix = create_date_matrix(start_date, end_date)
        self._pixels = pixel_art.PixelArt(text)
        check_text_and_date_fit(self._date_matrix, self._pixels.pixels)

        self.commit_matrix = [[], [], [], [], [], [], []]
        for column in range(0, len(self._date_matrix[0])):
            for row in range(0, len(self._date_matrix)):
                if column >= len(self._pixels.pixels[row]):
                    self.commit_matrix[row].append(
                        CommitMatrixElm(self._date_matrix[row][column], nb_commit_background))
                else:
                    self.commit_matrix[row].append(
                        CommitMatrixElm(self._date_matrix[row][column],
                                        nb_commit_foreground if (self._pixels.pixels[row][column]) else nb_commit_background
                                        ))
        return

def create_git_repo(dirPath):
    subprocess.run(['git', 'init'])

def add_file(filePath, startDate):
    if not os.path.exists(filePath):
        with open(filePath, 'w+') as f:
            f.write('')
        subprocess.run(['git', 'add', filePath])
        initial_date = startDate - datetime.timedelta(days=1)
        initial_date = datetime.datetime(year=initial_date.year, month=initial_date.month,
                                        day=initial_date.day, tzinfo=datetime.timezone.utc)
        subprocess.run(['git', 'commit', '-m', '"initial commit"', '--date', f'{initial_date.isoformat()}'])

def modify_file(filePath):
    with open(filePath, 'r') as f:
        data = f.read()
    with open(filePath, 'w') as f:
        if len(data):
            print('remove space')
            f.write('')
        else:
            print('add space')
            f.write(' ')
    return

def commit_modification(filePath, commitDate, commitNumber):
    subprocess.run(['git', 'add', filePath])
    subprocess.run(['git', 'commit',
                        '-m', f'"{commitDate.strftime("%Y-%m-%d")} commit #{commitNumber}"',
                        '--date', f'{commitDate.isoformat()}'])


scriptDir = os.path.dirname(os.path.realpath(__file__))
gitRepoDir = f'{scriptDir}/git_repo'
newFilePath = f'{gitRepoDir}/file.txt'
if not os.path.exists(gitRepoDir):
    os.makedirs(gitRepoDir)
os.chdir(gitRepoDir)
create_git_repo(gitRepoDir)
add_file(newFilePath, args.start_date)

cm = CommitMatrix(args.start_date, args.end_date, args.text,
                  args.nb_commit_background, args.nb_commit_foreground)

for col in range(0, len(cm.commit_matrix[0])):
    for row in range(0,7):
        if cm.commit_matrix[row][col].nb_commit > 0 and (cm.commit_matrix[row][col].date is not None):
            commit_date = cm.commit_matrix[row][col].date
            commit_date = datetime.datetime(year=commit_date.year, month=commit_date.month,
                                            day=commit_date.day, tzinfo=datetime.timezone.utc)

            for nb_commit in range(0, cm.commit_matrix[row][col].nb_commit):
                commit_date += datetime.timedelta(seconds=3)
                modify_file(newFilePath)
                commit_modification(newFilePath, commit_date, nb_commit)
exit(0)
