import os


def conversion(filename):
    if not os.path.exists('out'):
        os.makedirs('out')

    os.system('dcm2niix.exe ' +
              '-f %f_%d_%t ' +
              '-b y ' +
              '-d 9 ' +
              '-p n ' +
              '-z y ' +
              '-ba y ' +
              '-w 2 ' +
              '-o out/ ' +
              filename)
