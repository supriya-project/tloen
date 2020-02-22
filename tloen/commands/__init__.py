class ApplicationBoot:

    async def execute(self, harness):
        await harness.dsp_application.boot()


class ApplicationQuit:

    async def execute(self, harness):
        await harness.dsp_application.quit()


class TloenExit:

    async def execute(self, harness):
        await harness.dsp_application.quit()
        harness.tui_application.exit()
        harness.exit_future.set_result(True)
