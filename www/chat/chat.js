//Used for dynamic change of chat update time based on how often we are getting messages
chat_script="chat.pye"
chat_update_time=1000
min_chat_update_time=900
max_chat_update_time=3000
check_chat_update_rate=100
//We use the play_audio global variable to only play sounds on subsequent messages after the first load of all the previous messages.
play_audio=false

last_chat_time=0.0
oinkers=""
d=new Date();
d=d.getTimezoneOffset()*60
function updateChat(){
	$.post(chat_script,{"get":last_chat_time,"presence":$("#name").attr("value"),"tzoff":d},function(results){
		if (addMessage(results)==true){
			/*chat_update_time-=4*check_chat_update_rate
			if (chat_update_time<min_chat_update_time){
				chat_update_time=min_chat_update_time
			}*/
		}else{
			/*chat_update_time+=check_chat_update_rate
			if (chat_update_time>max_chat_update_time){
				chat_update_time=max_chat_update_time
			}*/
		}
		get_chat_timer=window.setTimeout(updateChat,chat_update_time);
		//We use the play_audio global variable to only play sounds on subsequent messages after the first load of all the previous messages.
		play_audio=true;
	}).fail(function(results){
		checkSessionTimedout(results.responseText)
	})
}

function sendChat(){
	//clearTimeout(get_chat_timer)
	$.post(chat_script,{"put":$("#message").attr("value"),"presence":$("#name").attr("value"),"get":last_chat_time},function(results){
		//addMessage(results)
		//chat_update_time=min_chat_update_time
		//get_chat_timer=window.setTimeout(updateChat,chat_update_time);
	})
	$("#message").attr("value","")	
}

function checkSessionTimedout(post_results){
	post_results=JSON.parse(post_results)
	if (post_results.error){
		if (post_results.error.code==401){
			$("#session_timeout").show();
		}
	}
}

function formatTime(seconds){
	var d=new Date(seconds*1000)
	
	var hr=d.getHours();
	var min = d.getMinutes();
	if (min < 10) {min = "0" + min;}
	var ampm = hr < 12 ? "am" : "pm";
	var sec=d.getSeconds();
	if (sec < 10) {sec = "0" + sec;}
	if (hr > 12){hr-=12;}
	
	return hr+":"+min+":"+sec+" "+ampm+" "+(d.getMonth()+1)+"/"+d.getDate()+"/"+String(d.getFullYear()).slice(2,4);
}

function updateScroll(){
	
}

function addMessage(post_results){
	//First calculate if we should auto-scroll when the new messages arrive
	total_area=0;
	lines=$("#chat_messages .chat_msg");
	//This function adds up all the heights of the chat lines so that if they get bigger the chat area will still scroll everything right
	lines.each(function(){
		var l=$(this);
		total_area+=l.outerHeight()+parseInt(l.css("margin-top"));
	})
	auto_scroll=true;
	if ($("#chat_messages").scrollTop()<total_area-$("#chat_messages").height()-15){
		//Don't auto-scroll if the user has scrolled up a little
		auto_scroll=false;
	}
	
	var post_results=JSON.parse(post_results);
	var new_messages="";
	for(var i=0;i<post_results["messages"].length;i++){
		d=new Date(post_results["messages"][i][0]*1000)
		new_messages+="<p class=\"chat_msg\"><span id=\""+parseInt(post_results["messages"][i][0])+"\" class=\"time\">"+formatTime(post_results["messages"][i][0])+"</span><span class=\"name\">"+post_results["messages"][i][1]+":</span><span class=\"msg\">"+post_results["messages"][i][2]+"</span></p>";
//		$("#chat_messages").append("<p class=\"chat_msg\"><span id=\""+parseInt(post_results["messages"][i][0])+"\" class=\"time\">"+formatTime(post_results["messages"][i][0])+"</span><span class=\"name\">"+post_results["messages"][i][1]+":</span><span class=\"msg\">"+post_results["messages"][i][2]+"</span></p>")
		
	}
	$("#chat_messages").append(new_messages);
	
	//Audio for new messages
	if (post_results["messages"].length>0 && document.getElementById("play-sound").checked==true && play_audio==true){
		var sound_elm=document.getElementById("sound")
		sound_elm.load()
		sound_elm.play()
	}
	
	//Parse list of online users
	$("ul.online-users-list").html("")
	for(var i=0;i<post_results["present"].length;i++){
		$("ul.online-users-list").append("<li>"+post_results["present"][i][1]+"</li>")
	}
	
	if (post_results["ct"]>0){
		last_chat_time=post_results["lct"];
		if (auto_scroll){
			total_area=0;
			lines=$("#chat_messages .chat_msg");
			//This function adds up all the heights of the chat lines so that if they get bigger the chat area will still scroll everything right
			lines.each(function(){
				var l=$(this);
				total_area+=l.outerHeight()+parseInt(l.css("margin-top"));
			})
			//total_area=lines.length*(lines.first().outerHeight()+parseInt(lines.first().css("margin-top")));
			$("#chat_messages").scrollTop(total_area-$("#chat_messages").height()+5)//+lines.first().css("margin-top"));
		}else{
			//Else flash the notification bar! :)
			$("#notification").fadeTo(600,1,function(){$("#notification").fadeTo(1800,0,"linear")});
		}
		return true;
	}
	
	return false;
}
		
$(document).ready(function(){
	$("#send_button").click(function(event){
		sendChat()
		event.preventDefault()
	})
	$("input").keydown(function(e){
		if (e.keyCode==13){
			sendChat()
		}
	})
	
	show_user_list=false
	$(".click-show .click-button").click(function(){
		if (!show_user_list){
			$(".click-show .disp-list").fadeIn("fast");
			$(".click-show .click-button").html("Hide Online Users")
			show_user_list=true
		}else{
			$(".click-show .disp-list").fadeOut("fast");
			$(".click-show .click-button").html("Show Online Users")
			show_user_list=false
		}
	})
	
	
	$("#chat_messages").on("click",".msg .timejump",function(e){
		$(this).css("background","red")
		console.log("clicked!")
		e.preventDefault();
		var id=$(this).attr("href")
		$("#chat_messages").animate({scrollTop: $(id).offset().top},"slow")
	})
	
	//Call the updateChat function just as if it had happened on a timed event and it will kick everything off (i.e. start the update loop)
	updateChat()
	

})