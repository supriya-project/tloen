import pytest
from uqbar.strings import normalize

from tloen.domain import Application


@pytest.mark.asyncio
async def test_1():
    application = Application()
    context = await application.add_context()
    track = await context.add_track()
    assert str(application) == normalize(
        f"""
        <Application [OFFLINE] {hex(id(application))}>
            <Transport>
            <Controllers>
            <Scenes>
            <Contexts>
                <Context <?> [?] {context.uuid}>
                    <Tracks [?]>
                        <Track [?] {track.uuid}>
                            <Clips>
                            <Slots>
                            <SubTracks [?]>
                            <Parameters [?]>
                                <BusParameter "gain" (0.0) [?] [?] {context.tracks[0].parameters["gain"].uuid}>
                                <BusParameter "panning" (0.0) [?] [?] {context.tracks[0].parameters["panning"].uuid}>
                            <SendTarget (0)>
                            <Receives [?]>
                            <Devices [?]>
                            <PreFaderSends [?]>
                            <PostFaderSends [?]>
                                <Send [?] {track.postfader_sends[0].uuid}>
                            <ReceiveTarget (0)>
                    <MasterTrack [?] {context.master_track.uuid}>
                        <Parameters [?]>
                            <BusParameter "gain" (0.0) [?] [?] {context.master_track.parameters["gain"].uuid}>
                        <SendTarget (1)>
                        <Receives [?]>
                        <Devices [?]>
                        <PreFaderSends [?]>
                        <PostFaderSends [?]>
                            <DirectOut [?] {context.master_track.postfader_sends[0].uuid}>
                        <ReceiveTarget (0)>
                    <CueTrack [?] {context.cue_track.uuid}>
                        <Parameters [?]>
                            <BusParameter "gain" (0.0) [?] [?] {context.cue_track.parameters["gain"].uuid}>
                            <BusParameter "mix" (0.0) [?] [?] {context.cue_track.parameters["mix"].uuid}>
                        <SendTarget (0)>
                        <Receives [?]>
                        <Devices [?]>
                        <PreFaderSends [?]>
                        <PostFaderSends [?]>
                            <DirectOut [?] {context.cue_track.postfader_sends[0].uuid}>
                        <ReceiveTarget (0)>
        """
    )


@pytest.mark.asyncio
async def test_2():
    application = Application()
    context = await application.add_context()
    track = await context.add_track()
    await application.boot()
    assert str(application) == normalize(
        f"""
        <Application [REALTIME] {hex(id(application))}>
            <Transport>
            <Controllers>
            <Scenes>
            <Contexts>
                <Context <RealtimeProvider <AsyncServer: udp://127.0.0.1:{context.provider.server.port}, 8i8o>> [{context.node_proxy.identifier}] {context.uuid}>
                    <Tracks [{context.tracks.node_proxy.identifier}]>
                        <Track [{track.node_proxy.identifier}] {track.uuid}>
                            <Clips>
                            <Slots>
                            <SubTracks [{track.tracks.node_proxy.identifier}]>
                            <Parameters [1009]>
                                <BusParameter "gain" (0.0) [1010] [0] {context.tracks[0].parameters["gain"].uuid}>
                                <BusParameter "panning" (0.0) [1011] [1] {context.tracks[0].parameters["panning"].uuid}>
                            <SendTarget (0)>
                            <Receives [{track.receives.node_proxy.identifier}]>
                            <Devices [{track.devices.node_proxy.identifier}]>
                            <PreFaderSends [{track.prefader_sends.node_proxy.identifier}]>
                            <PostFaderSends [{track.postfader_sends.node_proxy.identifier}]>
                                <Send [{track.postfader_sends[0].node_proxy.identifier}] {track.postfader_sends[0].uuid}>
                            <ReceiveTarget (0)>
                    <MasterTrack [{context.master_track.node_proxy.identifier}] {context.master_track.uuid}>
                        <Parameters [1022]>
                            <BusParameter "gain" (0.0) [1023] [2] {context.master_track.parameters["gain"].uuid}>
                        <SendTarget (1)>
                        <Receives [{context.master_track.receives.node_proxy.identifier}]>
                        <Devices [{context.master_track.devices.node_proxy.identifier}]>
                        <PreFaderSends [{context.master_track.prefader_sends.node_proxy.identifier}]>
                        <PostFaderSends [{context.master_track.postfader_sends.node_proxy.identifier}]>
                            <DirectOut [{context.master_track.postfader_sends[0].node_proxy.identifier}] {context.master_track.postfader_sends[0].uuid}>
                        <ReceiveTarget (0)>
                    <CueTrack [{context.cue_track.node_proxy.identifier}] {context.cue_track.uuid}>
                        <Parameters [1036]>
                            <BusParameter "gain" (0.0) [1037] [3] {context.cue_track.parameters["gain"].uuid}>
                            <BusParameter "mix" (0.0) [1038] [4] {context.cue_track.parameters["mix"].uuid}>
                        <SendTarget (0)>
                        <Receives [{context.cue_track.receives.node_proxy.identifier}]>
                        <Devices [{context.cue_track.devices.node_proxy.identifier}]>
                        <PreFaderSends [{context.cue_track.prefader_sends.node_proxy.identifier}]>
                        <PostFaderSends [{context.cue_track.postfader_sends.node_proxy.identifier}]>
                            <DirectOut [{context.cue_track.postfader_sends[0].node_proxy.identifier}] {context.cue_track.postfader_sends[0].uuid}>
                        <ReceiveTarget (0)>
        """
    )
