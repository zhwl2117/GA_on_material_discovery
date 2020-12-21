import subprocess


class Shell:
    def __init__(self, cmd):
        self.cmd = cmd
        self.ret_code = None
        self.ret_info = None
        self.err_info = None
        self._process = None

    def run_background(self):
        self._process = subprocess.Popen(self.cmd, shell=True,
                                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def get_status(self):
        ret_code = self._process.poll()
        if ret_code is None:
            status = "RUNNING"
        else:
            status = "FINISHED"
        return status

    def is_finished(self):
        ret_code = self._process.poll()
        if ret_code is None:
            return False
        else:
            return True

    def print_output(self):
        line = self._process.stdout.readline()  # 这儿会阻塞
        return line

    def kill(self):
        self._process.kill()


if __name__ == '__main__':
    shell = Shell('echo Hello')
    shell.run_background()
    # shell.kill()
    # print(shell.get_status())
    # shell.print_output()
    while not shell.is_finished():
        continue
    hello = shell.print_output()
    print(hello)
