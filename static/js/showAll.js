/**
 * Created by gzs3050 on 2014/11/13.
 */
$(document).ready(function() {
        $("#showmore").click(function () {
            $("#dialog").dialog("open");
            return false;
        });

        $("#dialog").dialog({
            autoOpen: false,
            show: "blind",
            hide: "explode",

            buttons: {
                "Ok": function() {
                    $(this).dialog("close");
                },
                "Cancel": function() {
                    $(this).dialog("close");
                }
          }
        })
    });


//            $("#dialog").dialog({
//               buttons: {"OK": function(){
//                   $(this).dialog("hide");
//               }}
//            });
//            var name = $(this).sibling("p.name").text();
//            var nickname = $(this).sibling("p.nickname").text();
//            var id = $(this).sibling("p.id").text();
//            var votes = $(this).sibling("p.votes").text();
//            var rank = $(this).sibling("p.rank").text();
//            var phone = $(this).sibling("p.phone").text();

            //$(this).attr("href", "anchor.html?name=" + name + "&nickname=" + nickname + "&id=" + id +
            //    "&votes=" + votes + "&rank=" + rank + "&phone=" + phone);

