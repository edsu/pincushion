# pincushion

*pincushion* is a command line tool for creating archives for resources on [Historypin]. It reads data from the Historypin API and writes a static website to a given directory. The file structure looks something like:

```
archive
├── collections
│   ├── my-collection
│   │   ├── image.jpg
│   │   └── index.html
│   ├── my-other-collection
│   │   ├── image.jpg
│   │   └── index.html
│   └── my-last-collection
│       ├── image.jpg
│       └── index.html
├── data.json
├── index.html
├── pins
│   ├── 123 
│   │   ├── image.jpg
│   │   └── index.html
│   ├── 456
│   │   ├── image.jpg
│   │   └── index.html
│   ├── 789 
│   │   ├── image.jpg
│   │   └── index.html
│   ├── 1001 
│   │   ├── index.html
│   │   └── media.mp3
│   └── 2112
│       ├── index.html
│       └── media.mp4
└── user.jpg
```

Each pin has its own directory, which contains the uploaded media (image, audio or video).

## Install

```shell
pip install pincushion
```

## Use

Create an archive for user 11670:

```
pincushion user --user-id 11670 --archive-path my-archive
```

Open the `my-archive/index.html` file in your browser.

[Historypin]: https://historypin.org
