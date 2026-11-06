% ANALYZE_SOUND_SPEED Reproduce all diagrams and numerical results for Q2.
% Run in MATLAB, without additional toolboxes:
%   run('/workspace/1/matlab/analyze_sound_speed.m')
% Or in GNU Octave, with a working graphics toolkit:
%   octave --no-gui --quiet /workspace/1/matlab/analyze_sound_speed.m
%
% The exercise specifies T and S, but not the depth interval. We choose
% z = 0:10:1000 m for illustration. Change z_values below if needed.
% Every depth curve keeps T and S fixed. These are idealized comparisons;
% actual T(z) and S(z) profiles can produce different gradients/sound channels.
% All assigned salinities are evaluated literally. The exercise does not
% give calibration limits or uncertainty; verify model validity for field use.

script_path = mfilename('fullpath');
code_dir = fileparts(script_path);
project_dir = fileparts(code_dir);
addpath(code_dir);
output_dir = fullfile(project_dir, 'results');
if ~exist(output_dir, 'dir')
    mkdir(output_dir);
end

T_values = 5:5:30;                 % degrees Celsius: six temperatures
S_values = 10:5:35;                % ppt: six salinities
z_values = (0:10:1000).';          % m: 101 depth samples, positive downward

% C has dimensions [depth, temperature, salinity].
C = zeros(numel(z_values), numel(T_values), numel(S_values));
for i = 1:numel(T_values)
    for j = 1:numel(S_values)
        C(:, i, j) = seawater_sound_speed(T_values(i), S_values(j), z_values);
    end
end

% Formula checks: a hand-calculated reference, depth slope, and all trends.
assert(abs(seawater_sound_speed(10, 35, 0) - 1489.99) < 1e-9);
assert(isequal(size(C), [numel(z_values), 6, 6]));
depth_steps = diff(C, 1, 1);
expected_depth_steps = 0.016 .* diff(z_values);
depth_errors = bsxfun(@minus, depth_steps, expected_depth_steps);
assert(max(abs(depth_errors(:))) < 1e-9);
depth_increment = C(end, :, :) - C(1, :, :);
assert(max(abs(depth_increment(:) - 0.016 * diff(z_values([1, end])))) < 1e-9);
assert(abs(seawater_sound_speed(10, 35, 1000) ...
    - seawater_sound_speed(10, 35, 0) - 16) < 1e-9);
temperature_steps = diff(C, 1, 2);
salinity_steps = diff(C, 1, 3);
assert(all(temperature_steps(:) > 0));
assert(all(salinity_steps(:) > 0));

[T_grid, S_grid] = ndgrid(T_values, S_values);
c_surface = seawater_sound_speed(T_grid, S_grid, 0);
c_at_1000 = seawater_sound_speed(T_grid, S_grid, 1000);
dc_dT = 4.6 - 0.11 .* T_grid + 0.00087 .* T_grid.^2 ...
    - 0.01 .* (S_grid - 35);       % (m/s) per degree Celsius
dc_dS = 1.34 - 0.01 .* T_grid;     % (m/s) per ppt
assert(all(dc_dT(:) > 0));
assert(all(dc_dS(:) > 0));
c_at_first_depth = seawater_sound_speed(T_grid, S_grid, z_values(1));
assert(max(abs(c_at_first_depth(:) - reshape(C(1, :, :), [], 1))) < 1e-9);

% Check vectorized broadcasting separately from the scalar loops above.
c_broadcast = seawater_sound_speed(T_values(:), S_values, 0);
assert(max(abs(c_broadcast(:) - c_surface(:))) < 1e-9);

% All 36 combinations, with explicitly labelled units.
summary_file = fullfile(output_dir, 'sound_speed_summary.csv');
fid = fopen(summary_file, 'w');
if fid < 0
    error('Cannot create %s', summary_file);
end
fprintf(fid, ['T_degC,S_ppt,c_z0_m_per_s,c_z1000_m_per_s,' ...
    'dc_dT_m_per_s_per_degC,dc_dS_m_per_s_per_ppt,dc_dz_per_s\n']);
for i = 1:numel(T_values)
    for j = 1:numel(S_values)
        fprintf(fid, '%.10g,%.10g,%.10f,%.10f,%.10f,%.10f,%.10f\n', ...
            T_values(i), S_values(j), c_surface(i, j), c_at_1000(i, j), ...
            dc_dT(i, j), dc_dS(i, j), 0.016);
    end
end
fclose(fid);

% Full data for every plotted point: 6 * 6 * 101 = 3636 rows.
profiles_file = fullfile(output_dir, 'sound_speed_profiles.csv');
fid = fopen(profiles_file, 'w');
if fid < 0
    error('Cannot create %s', profiles_file);
end
fprintf(fid, 'T_degC,S_ppt,z_m,c_m_per_s\n');
for i = 1:numel(T_values)
    for j = 1:numel(S_values)
        for k = 1:numel(z_values)
            fprintf(fid, '%.10g,%.10g,%.10g,%.10f\n', ...
                T_values(i), S_values(j), z_values(k), C(k, i, j));
        end
    end
end
fclose(fid);

% Identical axes across all panels make the parameter shifts comparable.
c_limits = [5 * floor(min(C(:))/5), 5 * ceil(max(C(:))/5)];
z_limits = [z_values(1), z_values(end)];
colors = lines(6);
S_labels = cell(1, 6);
T_labels = cell(1, 6);
for j = 1:6
    S_labels{j} = sprintf('S = %g ppt', S_values(j));
    T_labels{j} = sprintf('T = %g deg C', T_values(j));
end

% Figure 1: six fixed-temperature panels; salinity varies within each panel.
fig1 = figure('Visible', 'off', 'Color', 'w', ...
    'Position', [50, 50, 1400, 900]);
for i = 1:6
    subplot(2, 3, i);
    hold on;
    for j = 1:6
        plot(C(:, i, j), z_values, 'Color', colors(j, :), 'LineWidth', 1.5);
    end
    hold off;
    set(gca, 'YDir', 'reverse', 'FontSize', 10);
    xlim(c_limits);
    ylim(z_limits);
    grid on;
    xlabel('Sound speed c (m/s)');
    ylabel('Depth z (m)');
    title(sprintf('Fixed T = %g deg C', T_values(i)));
    if i <= 3
        legend(S_labels, 'Location', 'southeast');
    else
        legend(S_labels, 'Location', 'southwest');
    end
end
print(fig1, fullfile(output_dir, '01_depth_profiles_fixed_temperature.png'), ...
    '-dpng', '-r160');
close(fig1);

% Figure 2: six fixed-salinity panels; temperature varies within each panel.
fig2 = figure('Visible', 'off', 'Color', 'w', ...
    'Position', [50, 50, 1400, 900]);
for j = 1:6
    subplot(2, 3, j);
    hold on;
    for i = 1:6
        plot(C(:, i, j), z_values, 'Color', colors(i, :), 'LineWidth', 1.5);
    end
    hold off;
    set(gca, 'YDir', 'reverse', 'FontSize', 10);
    xlim(c_limits);
    ylim(z_limits);
    grid on;
    xlabel('Sound speed c (m/s)');
    ylabel('Depth z (m)');
    title(sprintf('Fixed S = %g ppt', S_values(j)));
    legend(T_labels, 'Location', 'southwest');
end
print(fig2, fullfile(output_dir, '02_depth_profiles_fixed_salinity.png'), ...
    '-dpng', '-r160');
close(fig2);

% Figure 3: surface dependence on temperature and salinity at z = 0 m.
fig3 = figure('Visible', 'off', 'Color', 'w', ...
    'Position', [50, 50, 1000, 750]);
surf(T_grid, S_grid, c_surface, 'EdgeColor', [0.2, 0.2, 0.2], ...
    'FaceColor', 'interp');
xlabel('Temperature T (deg C)');
ylabel('Salinity S (ppt)');
zlabel('Sound speed c (m/s)');
title('Temperature and salinity dependence at z = 0 m');
grid on;
view(135, 25);
colorbar;
print(fig3, fullfile(output_dir, '03_temperature_salinity_surface.png'), ...
    '-dpng', '-r160');
close(fig3);

fprintf('All numerical checks passed.\n');
fprintf('Computed %d T-S combinations and %d depth samples each.\n', ...
    numel(T_values) * numel(S_values), numel(z_values));
fprintf('c range over the selected grid: %.5f to %.5f m/s.\n', min(C(:)), max(C(:)));
fprintf('dc/dT range: %.5f to %.5f (m/s)/deg C.\n', min(dc_dT(:)), max(dc_dT(:)));
fprintf('dc/dS range: %.5f to %.5f (m/s)/ppt.\n', min(dc_dS(:)), max(dc_dS(:)));
fprintf('dc/dz = 0.016 (m/s)/m; c(1000)-c(0) = 16 m/s.\n');
fprintf('Figures and CSV data saved to: %s\n', output_dir);
