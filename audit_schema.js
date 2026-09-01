() => {
  // Mirrors the live panel: AIMBOT really has 13 controls of mixed types, which
  // is what tipped it over the old item-count rule for two columns.
  schema = [
    {type:'toggle',  tab:'Combat', section:'AIMBOT', name:'Enable Aimbot', flag:'AimbotToggle', desc:'自动瞄准总开关'},
    {type:'dropdown',tab:'Combat', section:'AIMBOT', name:'Aim Mode', flag:'AimModeDropdown', options:['Silent Aim','Right Click Lock'], desc:'决定下方哪些选项可用'},
    {type:'dropdown',tab:'Combat', section:'AIMBOT', name:'Target Priority', flag:'TargetModeDropdown', options:['Screen Distance','Player Distance'], desc:'先打离准星近的还是离你近的'},
    {type:'dropdown',tab:'Combat', section:'AIMBOT', name:'Wallbang', flag:'WallbangModeDropdown', options:['Off','Normal','Dangerous'], desc:'Normal=按真实穿透值算；Dangerous=无视墙体，站原地就能清出生点，很显眼'},
    {type:'toggle',  tab:'Combat', section:'AIMBOT', name:'No Recoil', flag:'NoRecoilToggle'},
    {type:'toggle',  tab:'Combat', section:'AIMBOT', name:'Multi-Hit', flag:'MultiHitToggle', desc:'一枪子弹命中多个目标'},
    {type:'toggle',  tab:'Combat', section:'AIMBOT', name:'Auto Shoot', flag:'AutoShootToggle', desc:'锁定目标后自动开火'},
    {type:'toggle',  tab:'Combat', section:'AIMBOT', name:'Rapid Fire', flag:'RapidFireToggle', risk:true, desc:'破坏射速限制，服务器会校验'},
    {type:'toggle',  tab:'Combat', section:'AIMBOT', name:'Force Auto', flag:'ForceAutoToggle', desc:'让半自动武器连发'},
    {type:'toggle',  tab:'Combat', section:'AIMBOT', name:'Wallbang (RCL)', flag:'WallbangRCLToggle'},
    {type:'toggle',  tab:'Combat', section:'AIMBOT', name:'Show FOV Circle', flag:'FOVToggle'},
    {type:'slider',  tab:'Combat', section:'AIMBOT', name:'FOV Radius', flag:'FOVSlider', min:50, max:500, suffix:'px'},
    {type:'slider',  tab:'Combat', section:'AIMBOT', name:'Smoothing', flag:'AimbotSmoothing', min:1, max:10},
    {type:'toggle',  tab:'Movement', section:'MOVEMENT', name:'Bunny Hop', flag:'BhopToggle', desc:'落地瞬间自动起跳'},
    {type:'toggle',  tab:'Movement', section:'MOVEMENT', name:'Air Strafe', flag:'AirStrafeToggle', desc:'空中转视角加速'},
    {type:'toggle',  tab:'Movement', section:'MOVEMENT', name:'Counter-Strafe', flag:'CounterStrafeToggle', desc:'松键急停'},
    {type:'keybind', tab:'Settings', section:'UI CONTROL', name:'Panic Key', flag:'PanicKey', default:'END'},
  ];
  const guns = ['M4A4','AK-47','AWP','Desert Eagle','USP-S','Glock','P90','MP9','Nova','AUG',
                'FAMAS','Galil','SG 553','M4A1-S','XM1014','P250','Five-SeveN','MAC-10','Tec-9','SSG 08'];
  guns.forEach((n,i)=>schema.push({type:'dropdown',tab:'Misc',section:'SKIN CHANGER',
      name:n, flag:'Skin'+i, options:['Stock','Vanilla','Howl']}));
  flags = {AimbotToggle:true, AimModeDropdown:'Silent Aim', TargetModeDropdown:'Screen Distance',
           WallbangModeDropdown:'Off', NoRecoilToggle:true, MultiHitToggle:false,
           AutoShootToggle:true, RapidFireToggle:false, ForceAutoToggle:false,
           WallbangRCLToggle:false, FOVToggle:false, FOVSlider:210, AimbotSmoothing:2,
           BhopToggle:true, AirStrafeToggle:true, CounterStrafeToggle:false, PanicKey:'END'};
  guns.forEach((n,i)=>flags['Skin'+i]='Stock');
  luaConnected = true; schemaSig=''; rebuildIfSchemaChanged(); applyAllFlags();
  window.__ws_onmessage({data: JSON.stringify({type:'flag', flag:'_visibility',
    value:{WallbangRCLToggle:false, FOVToggle:false, FOVSlider:false, AimbotSmoothing:false}})});
}
