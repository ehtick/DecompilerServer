using ModelContextProtocol.Client;

namespace Tests;

public class ToolAnnotationTests
{
    [Fact]
    public async Task StdioToolsList_DeclaresReadOnlyInspectionAndStateChangingTools()
    {
        using var timeout = new CancellationTokenSource(TimeSpan.FromSeconds(30));
        await using var client = await McpClient.CreateAsync(
            new StdioClientTransport(new StdioClientTransportOptions
            {
                Command = "dotnet",
                Arguments = [typeof(DecompilerServer.Program).Assembly.Location]
            }), cancellationToken: timeout.Token);

        var tools = await client.ListToolsAsync(cancellationToken: timeout.Token);
        var mutations = new HashSet<string>(StringComparer.Ordinal)
        {
            "load_assembly", "unload", "select_context", "set_decompile_settings",
            "clear_caches", "warm_index"
        };
        Assert.Contains(tools, tool => tool.Name == "get_decompiled_source");
        Assert.Contains(tools, tool => tool.Name == "search_symbols");
        foreach (var name in mutations)
            Assert.Contains(tools, tool => tool.Name == name);

        foreach (var tool in tools)
        {
            var expected = !mutations.Contains(tool.Name);
            Assert.True(tool.ProtocolTool.Annotations?.ReadOnlyHint == expected,
                $"{tool.Name} must advertise readOnlyHint={expected} over stdio.");
        }
    }
}
