package dev.beevisual;

import dev.beevisual.gui.ClickGuiScreen;
import dev.beevisual.module.ModuleManager;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.keybinding.v1.KeyBindingHelper;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayConnectionEvents;
import net.fabricmc.fabric.api.client.rendering.v1.HudRenderCallback;
import net.fabricmc.fabric.api.event.player.AttackEntityCallback;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.option.KeyBinding;
import net.minecraft.client.util.InputUtil;
import net.minecraft.util.ActionResult;
import org.lwjgl.glfw.GLFW;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class BeeVisual implements ClientModInitializer {
    public static final Logger LOG = LoggerFactory.getLogger("BeeVisual");
    public static KeyBinding GUI_KEY;
    public static KeyBinding ZOOM_KEY;

    @Override
    public void onInitializeClient() {
        GUI_KEY = KeyBindingHelper.registerKeyBinding(new KeyBinding(
                "key.beevisual.gui", InputUtil.Type.KEYSYM, GLFW.GLFW_KEY_RIGHT_SHIFT, "category.beevisual"));
        ZOOM_KEY = KeyBindingHelper.registerKeyBinding(new KeyBinding(
                "key.beevisual.zoom", InputUtil.Type.KEYSYM, GLFW.GLFW_KEY_C, "category.beevisual"));

        ModuleManager.init();
        ModuleManager.load();

        ClientTickEvents.END_CLIENT_TICK.register(mc -> {
            Stats.tick(mc);
            while (GUI_KEY.wasPressed()) {
                if (mc.currentScreen == null) mc.setScreen(new ClickGuiScreen());
            }
            if (mc.player != null && mc.world != null) ModuleManager.tick();
        });

        HudRenderCallback.EVENT.register((ctx, tickCounter) -> {
            MinecraftClient mc = MinecraftClient.getInstance();
            if (mc.options.hudHidden || mc.player == null) return;
            ModuleManager.hud(ctx, mc.getWindow().getScaledWidth(), mc.getWindow().getScaledHeight());
        });

        AttackEntityCallback.EVENT.register((player, world, hand, entity, hit) -> {
            if (world.isClient()) Stats.onAttack(entity);
            return ActionResult.PASS;
        });

        ClientPlayConnectionEvents.JOIN.register((handler, sender, client) -> Stats.reset());

        LOG.info("BeeVisual loaded: {} modules", ModuleManager.ALL.size());
    }
}
