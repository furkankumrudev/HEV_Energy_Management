%% GENERATE REPRODUCIBLE FIGURES FOR THE WORD REPORT

projectDir = fileparts(mfilename('fullpath'));
fis = readfis(fullfile(projectDir, 'HEV_Energy_Management.fis'));
outputDir = fullfile(projectDir, 'report_figures');
if ~isfolder(outputDir)
    mkdir(outputDir);
end

surfaceDefinitions = {
    [1 2], [NaN NaN 60],  'surface_soc_torque.png', ...
        'Battery SoC (%)', 'Torque demand (%)';
    [1 3], [NaN 60 NaN],  'surface_soc_trip.png', ...
        'Battery SoC (%)', 'Trip distance (km)';
    [2 3], [50 NaN NaN],  'surface_torque_trip.png', ...
        'Torque demand (%)', 'Trip distance (km)';
};

for i = 1:size(surfaceDefinitions, 1)
    options = gensurfOptions;
    options.InputIndex = surfaceDefinitions{i, 1};
    options.OutputIndex = 1;
    options.NumGridPoints = [41 41];
    options.ReferenceInputs = surfaceDefinitions{i, 2};
    [xGrid, yGrid, outputGrid] = gensurf(fis, options);

    figureHandle = figure('Visible', 'off', 'Color', 'white', ...
        'Position', [100 100 1100 650]);
    surf(xGrid, yGrid, outputGrid, 'EdgeColor', [0.25 0.25 0.25]);
    xlabel(surfaceDefinitions{i, 4});
    ylabel(surfaceDefinitions{i, 5});
    zlabel('Electric power share');
    zlim([0 1]);
    caxis([0 1]);
    colormap(parula);
    colorbar;
    grid on;
    view(135, 28);
    exportgraphics(figureHandle, ...
        fullfile(outputDir, surfaceDefinitions{i, 3}), 'Resolution', 200);
    close(figureHandle);
end

figureHandle = figure('Visible', 'off', 'Color', 'white', ...
    'Position', [100 100 1000 550]);
plotmf(fis, "output", 1, 401);
xlabel('Electric power share');
ylabel('Membership degree');
title('Power-split output membership functions');
grid on;
exportgraphics(figureHandle, fullfile(outputDir, 'output_membership.png'), ...
    'Resolution', 200);
close(figureHandle);

figureHandle = figure('Visible', 'off', 'Color', 'white', ...
    'Position', [100 100 1400 850]);
plotrule(fis, Inputs=[60 60 100], NumSamplePoints=401);
exportgraphics(figureHandle, fullfile(outputDir, 'reference_scenario.png'), ...
    'Resolution', 200);
close(figureHandle);

fprintf('Report figures written to %s\n', outputDir);
