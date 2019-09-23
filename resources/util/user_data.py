import os

DATA_DIR = "/home/{username}/.resources/".format(username=os.getlogin())


def read(filename: str) -> dict:
    try:
        file = open(DATA_DIR + filename, 'r')
        return {
            line_split[0]: line_split[1]
            for line_split in [
                line.split('=') for line in file.readlines()
            ]
        }

    except FileNotFoundError:
        return dict()


def write(filename: str, data: dict) -> None:
    # set value
    current_data = read(filename)
    current_data.update(data)

    # get full path
    full_path = DATA_DIR + filename
    dirname = full_path[:full_path.rfind('/')]

    # create directories if necessary
    os.makedirs(dirname, exist_ok=True)

    # write
    file = open(full_path, 'w+')
    file.writelines([f"{key}={value}" for key, value in current_data.items()])


def get_hours(year, month) -> dict:
    return read(f"{year}/{month}")


def set_hours(year, month, hours: dict) -> None:
    write(f"{year}/{month}", hours)
