function PrismLayerStudio()
%PRISMLAYERSTUDIO Open the complete offline CFD prism-layer calculator from MATLAB.
% Usage:
%   addpath('path/to/PrismLayerStudio/matlab');
%   PrismLayerStudio
% This is a MATLAB launcher for the HTML/JS app, not a native .mltbx package.
    homeFolder = fileparts(fileparts(mfilename('fullpath')));
    htmlFile = fullfile(homeFolder, 'app', 'index.html');
    assert(isfile(htmlFile), '找不到 app/index.html，请保持压缩包目录结构。');
    fileUrl = ['file:///' strrep(htmlFile, '\', '/')];
    web(fileUrl, '-browser');
end
