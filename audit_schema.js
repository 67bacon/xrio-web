() => {
  schema = [
    {type:'toggle',  tab:'Combat', section:'AIMBOT', name:'Enable Aimbot', flag:'AimbotToggle', desc:'自动瞄准总开关'},
    {type:'dropdown',tab:'Combat', section:'AIMBOT', name:'Aim Mode', flag:'AimModeDropdown', options:['Silent Aim','Right Click Lock']},
    {type:'dropdown',tab:'Combat', section:'AIMBOT', name:'Wallbang', flag:'WallbangModeDropdown', options:['Off','Normal','Dangerous'], desc:'三选一'},
    {type:'toggle',  tab:'Combat', section:'AIMBOT', name:'No Recoil', flag:'NoRecoilToggle', desc:'消除后坐力'},
    {type:'toggle',  tab:'Combat', section:'AIMBOT', name:'Multi-Hit', flag:'MultiHitToggle', desc:'一枪命中多个'},
    {type:'toggle',  tab:'Combat', section:'AIMBOT', name:'Auto Shoot', flag:'AutoShootToggle', desc:'锁定后自动开火'},
    {type:'toggle',  tab:'Combat', section:'AIMBOT', name:'Rapid Fire', flag:'RapidFireToggle', risk:true, desc:'服务器会校验'},
    {type:'slider',  tab:'Combat', section:'AIMBOT', name:'FOV Radius', flag:'FOVSlider', min:50, max:500, suffix:'px'},
    {type:'toggle',  tab:'Movement', section:'MOVEMENT', name:'Bunny Hop', flag:'BhopToggle', desc:'落地瞬间自动起跳'},
    {type:'toggle',  tab:'Movement', section:'MOVEMENT', name:'Air Strafe', flag:'AirStrafeToggle', desc:'空中转视角加速'},
    {type:'toggle',  tab:'Movement', section:'MOVEMENT', name:'Counter-Strafe', flag:'CounterStrafeToggle', desc:'松键急停'},
    {type:'keybind', tab:'Settings', section:'UI CONTROL', name:'Panic Key', flag:'PanicKey', default:'END'},
  ];
  for (let i=0;i<20;i++) schema.push({type:'dropdown',tab:'Misc',section:'SKIN CHANGER',
      name:['M4A4','AK-47','AWP','Desert Eagle','USP-S','Glock','P90','MP9','Nova','AUG',
            'FAMAS','Galil','SG 553','M4A1-S','XM1014','P250','Five-SeveN','MAC-10','Tec-9','SSG 08'][i],
      flag:'Skin'+i, options:['Stock','Vanilla','Howl']});
  flags = {AimbotToggle:true, AimModeDropdown:'Silent Aim', WallbangModeDropdown:'Normal',
           NoRecoilToggle:true, MultiHitToggle:true, AutoShootToggle:true,
           RapidFireToggle:false, FOVSlider:210, BhopToggle:true, AirStrafeToggle:true,
           CounterStrafeToggle:false, PanicKey:'END'};
  for (let i=0;i<20;i++) flags['Skin'+i]='Stock';
  luaConnected = true; schemaSig=''; rebuildIfSchemaChanged(); applyAllFlags();
}
