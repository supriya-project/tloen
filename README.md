# Tloen: A DAW for Supriya

Tloen is a pre-alpha DAW framework built on top of Python 3's
[asyncio](https://docs.python.org/3/library/asyncio.html) and
[Supriya](https://github.com/josiah-wolf-oberholtzer/supriya), 
with a domain model inspired by Ableton Live.

Current development is focused on solidifying and testing the core domain
model, and fleshing out a JSON API.


## Install

- Get Supriya:

  ```
  git clone https://github.com/josiah-wolf-oberholtzer/supriya.git
  ```

- Install Supriya (from within your clone):

  ```
  pip3 install -e .[cython]
  ```

- Get Tloen:

  ```
  git clone https://github.com/josiah-wolf-oberholtzer/tloen.git

- Install Tloen (from within your clone):

  ```
  pip3 install -e .[test]
  ```

## Example

Because Tloen runs in an asyncio event loop, use Python 3.8+'s asyncio REPL if
you want to experiment interactively:

```
python3 -m asyncio
```

- Import Tloen:

  ```
  >>> import tloen
  ```

- Create an application:

  ```
  >>> app = tloen.Application()
  ```

- Add a context:

  ```
  >>> context = await app.add_context()
  ```

  Contexts govern a single instance of `scsynth`. Tracks can be distributed
  across multiple contexts for optimizing CPU usage.

- Add a track:

  ```
  >>> track = await context.add_track()
  ```

- Add an instrument to the track:

  ```
  >>> instrument = await track.add_device(tloen.domain.Instrument)
  ```

- Boot the application and query the `scsynth` node tree of the context:
  ```
  >>> await app.boot()
  <tloen.domain.applications.Application object at 0x7fb0f12b4460>
  >>> print(await context.query())
  NODE TREE 1000 group (Context)
      1001 group (Tracks)
          1002 group (Track)
              1009 group (Parameters)
                  1010 group (gain)
                  1011 group (panning)
              1012 group (Receives)
              1003 None (Input)
              1008 group (SubTracks)
              1004 None (InputLevels)
              1013 group (Devices)
                  1014 group (Instrument)
                      1016 None (DeviceIn)
                      1015 group (Body)
                      1017 None (DeviceOut)
              1005 None (PrefaderLevels)
              1018 group (PreFaderSends)
              1006 None (Output)
              1019 group (PostFaderSends)
                  1033 None (Send)
              1007 None (PostfaderLevels)
      1020 group (MasterTrack)
          1026 group (Parameters)
              1027 group (gain)
          1028 group (Receives)
          1021 None (Input)
          1022 None (InputLevels)
          1029 group (Devices)
          1023 None (PrefaderLevels)
          1030 group (PreFaderSends)
          1024 None (Output)
          1031 group (PostFaderSends)
              1032 None (DirectOut)
          1025 None (PostfaderLevels)
      1034 group (CueTrack)
          1040 group (Parameters)
              1041 group (gain)
              1042 group (mix)
          1043 group (Receives)
          1035 None (Input)
          1036 None (InputLevels)
          1044 group (Devices)
          1037 None (PrefaderLevels)
          1045 group (PreFaderSends)
          1038 None (Output)
          1046 group (PostFaderSends)
              1047 None (DirectOut)
          1039 None (PostfaderLevels)
  ```

- Add a scene to the application, then add a clip to the corresponding slot in
  the track:
  ```
  >>> scene = await app.add_scene()
  >>> clip = await track.slots[0].add_clip(notes=[
  ...     tloen.domain.Note(0, 0.25, pitch=64),
  ...     tloen.domain.Note(0.5, 0.75, pitch=67),
  ... ])
  ```

- Fire the slot and listen:
  ```
  >>> await track.slots[0].fire()
  ```

- Stop the music:
  ```
  >>> await track.stop()
  ```
