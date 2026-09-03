# largest-files

递归扫描目录，并按字节数列出最大的文件（默认 10 个）。符号链接不会被跟随。

```console
$ largest-files /path/to/directory
1048576\t/path/to/directory/archive.bin
```

使用 `-n` 或 `--count` 可以修改结果数量：

```console
$ largest-files --count 5 /path/to/directory
```
