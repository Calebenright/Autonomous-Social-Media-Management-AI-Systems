$(document).ready(function(){
    'use strict';

    /* --------------------------------------------------------------------- */
    /* WOW
    /* --------------------------------------------------------------------- */
    var wow = new WOW(
      {
        boxClass:     'wow',      // animated element css class (default is wow)
        animateClass: 'animated', // animation css class (default is animated)
        offset:       80,          // distance to the element when triggering the animation (default is 0)
        mobile:       true,       // trigger animations on mobile devices (default is true)
        live:         true,       // act on asynchronously loaded content (default is true)
        callback:     function(box) {
          // the callback is fired every time an animation is started
          // the argument that is passed in is the DOM node being animated
        },
        scrollContainer: null // optional scroll container selector, otherwise use window
      }
    );
    wow.init();




    /* --------------------------------------------------------------------- */
    /* preloaderKDZ
    /* --------------------------------------------------------------------- */
        $("#preloaderKDZ").delay(450).fadeOut(950);






    /* --------------------------------------------------------------------- */
    /* CAROUSEL
    /* --------------------------------------------------------------------- */
    function sofani_init_owl_carousel() {

        $('.sofani-owl-carousel').each(function () {

            var $this = $(this),
                $loop = $this.attr('data-loop') == 'yes',
                $numberItem = parseInt($this.attr('data-number')),
                $Nav = $this.attr('data-navcontrol') == 'yes',
                $Dots = $this.attr('data-dots') == 'yes',
                $autoplay = $this.attr('data-autoplay') == 'yes',
                $autoplayTimeout = parseInt($this.attr('data-autoplaytimeout')),
                $marginItem = parseInt($this.attr('data-margin')),
                $rtl = $this.attr('data-rtl') == 'yes',
                $autoHeight = $this.attr('data-autoheight') == 'yes',
                $resNumber = {
                    0: {
                        items: 1
                    }
                }; // Responsive Settings

            $numberItem = (isNaN($numberItem)) ? 1 : $numberItem;
            $autoplayTimeout = (isNaN($autoplayTimeout)) ? 6000 : $autoplayTimeout;
            $marginItem = (isNaN($marginItem)) ? 0 : $marginItem;

            if (!$this.is('.owl-carousel')) {
                $this.addClass('owl-carousel');
            }

            //console.log($Nav);

            switch ($numberItem) {

                case 1 :
                    $resNumber = {
                        0: {
                            items: 1
                        }
                    }
                    break;

                case 2 :
                    $resNumber = {
                        0: {
                            items: 1
                        },
                        480: {
                            items: 1
                        },
                        768: {
                            items: 2
                        },
                        992: {
                            items: $numberItem
                        }
                    }
                    break;

                case 3 :
                case 4 :
                    $resNumber = {
                        0: {
                            items: 1
                        },
                        480: {
                            items: 2
                        },
                        768: {
                            items: 2
                        },
                        992: {
                            items: 3
                        },
                        1200: {
                            items: $numberItem
                        }
                    }
                    break;

                default : // $numberItem > 4
                    $resNumber = {
                        0: {
                            items: 1
                        },
                        480: {
                            items: 2
                        },
                        768: {
                            items: 3
                        },
                        992: {
                            items: 3
                        },
                        1200: {
                            items: 4
                        },
                        1500: {
                            items: 5
                        },
                        1800: {
                            items: $numberItem
                        }
                    }
                    break;
            } // Endswitch


            $(this).owlCarousel({
                items: $numberItem,
                loop: $loop,
                nav: $Nav,
                navText: ['<span class="fa fa-angle-left"></span>', '<span class="fa fa-angle-right"></span>'],
                navContainer: false,
                dots: $Dots,
                autoplay: $autoplay,
                autoplayTimeout: $autoplayTimeout,
                autoHeight: $autoHeight,
                margin: $marginItem,
                //responsiveClass:true,
                rtl: $rtl,
                responsive: $resNumber,
                autoplayHoverPause: true,

                //center: true,
                onRefreshed: function () {
                    var total_active = $this.find('.owl-item.active').length;
                    var i = 0;

                    $this.find('.owl-item').removeClass('active-first active-last');
                    $this.find('.owl-item.active').each(function () {
                        i++;
                        if (i == 1) {
                            $(this).addClass('active-first');
                        }
                        if (i == total_active) {
                            $(this).addClass('active-last');
                        }
                    });
                },
                onTranslated: function () {
                    var total_active = $this.find('.owl-item.active').length;
                    var i = 0;

                    $this.find('.owl-item').removeClass('active-first active-last');
                    $this.find('.owl-item.active').each(function () {
                        i++;
                        if (i == 1) {
                            $(this).addClass('active-first');
                        }
                        if (i == total_active) {
                            $(this).addClass('active-last');
                        }
                    });
                },
                onResized: function () {
                    //essence_set_equal_columns();
                }
            });

        });
    }
    if($('.product-thumbs').length){
        sofani_init_owl_carousel();
    }
      // carousel2
      function begreen_2_carousel() {

        var sync1 = $("#sync1");
        var sync2 = $("#sync2");
        var slidesPerPage = 4; 
        var syncedSecondary = true;

        sync1.owlCarousel({
          items : 1,
          slideSpeed : 2000,
          nav: true,
          autoplay: false,
          dots: true,
          loop: true,
          responsiveRefreshRate : 200,
          navText: ['<span class="fa fa-angle-left"></span>', '<span class="fa fa-angle-right"></span>'],
        }).on('changed.owl.carousel', syncPosition);

        sync2
          .on('initialized.owl.carousel', function () {
            sync2.find(".owl-item").eq(0).addClass("current");
          })
          .owlCarousel({
          items : slidesPerPage,
          dots: true,
          nav: true,
          smartSpeed: 200,
          slideSpeed : 500,
          slideBy: slidesPerPage, 
          responsiveRefreshRate : 100
        }).on('changed.owl.carousel', syncPosition2);

        function syncPosition(el) {
          var count = el.item.count-1;
          var current = Math.round(el.item.index - (el.item.count/2) - .5);
          
          if(current < 0) {
            current = count;
          }
          if(current > count) {
            current = 0;
          }
          
          //end block

          sync2
            .find(".owl-item")
            .removeClass("current")
            .eq(current)
            .addClass("current");
          var onscreen = sync2.find('.owl-item.active').length - 1;
          var start = sync2.find('.owl-item.active').first().index();
          var end = sync2.find('.owl-item.active').last().index();
          
          if (current > end) {
            sync2.data('owl.carousel').to(current, 100, true);
          }
          if (current < start) {
            sync2.data('owl.carousel').to(current - onscreen, 100, true);
          }
        }
        
        function syncPosition2(el) {
          if(syncedSecondary) {
            var number = el.item.index;
            sync1.data('owl.carousel').to(number, 100, true);
          }
        }
        
        sync2.on("click", ".owl-item", function(e){
          e.preventDefault();
          var number = $(this).index();
          sync1.data('owl.carousel').to(number, 300, true);
        });
      }
      // carousel3
      function begreen_3_carousel() {

        var syncs1 = $("#syncs1");
        var syncs2 = $("#syncs2");
        var slidesPerPage = 6; 
        var syncedSecondary = true;

        syncs1.owlCarousel({
          items : 1,
          slideSpeed : 2000,
          nav: true,
          autoplay: false,
          dots: true,
          loop: true,
          responsiveRefreshRate : 200,
          navText: ['<span class="fa fa-angle-left"></span>', '<span class="fa fa-angle-right"></span>'],
        }).on('changed.owl.carousel', syncPosition);

        syncs2
          .on('initialized.owl.carousel', function () {
            syncs2.find(".owl-item").eq(0).addClass("current");
          })
          .owlCarousel({
          items : slidesPerPage,
          dots: true,
          nav: true,
          smartSpeed: 200,
          slideSpeed : 500,
          slideBy: slidesPerPage, 
          responsiveRefreshRate : 100
        }).on('changed.owl.carousel', syncPosition2);

        function syncPosition(el) {
          var count = el.item.count-1;
          var current = Math.round(el.item.index - (el.item.count/2) - .5);
          
          if(current < 0) {
            current = count;
          }
          if(current > count) {
            current = 0;
          }
          
          //end block

          syncs2
            .find(".owl-item")
            .removeClass("current")
            .eq(current)
            .addClass("current");
          var onscreen = syncs2.find('.owl-item.active').length - 1;
          var start = syncs2.find('.owl-item.active').first().index();
          var end = syncs2.find('.owl-item.active').last().index();
          
          if (current > end) {
            syncs2.data('owl.carousel').to(current, 100, true);
          }
          if (current < start) {
            syncs2.data('owl.carousel').to(current - onscreen, 100, true);
          }
        }
        
        function syncPosition2(el) {
          if(syncedSecondary) {
            var number = el.item.index;
            syncs1.data('owl.carousel').to(number, 100, true);
          }
        }
        
        syncs2.on("click", ".owl-item", function(e){
          e.preventDefault();
          var number = $(this).index();
          syncs1.data('owl.carousel').to(number, 300, true);
        });
      }




    /* --------------------------------------------------------------------- */
    /* hoverdir
    /* --------------------------------------------------------------------- */
    $('.da-thumbs > li').each( function() { $(this).hoverdir(); } );





    
    /* --------------------------------------------------------------------- */
    /* MMENU MENU MOBILE
    /* --------------------------------------------------------------------- */
      $('#primary-menu').mmenu({
          extensions: ['effect-slide-menu', 'pageshadow'],
          navbar: {
              title: 'Menu'
          },
          navbars: [
              {
                  position: 'top',
                  content: [
                      'prev',
                      'title',
                      'close'
                  ]
              }
          ]
      }, {
          // configuration
          clone: true
      });






    /* --------------------------------------------------------------------- */
    /* SIDEBAR FOLLOWME
    /* --------------------------------------------------------------------- */
    $(document).on('click', function(event) {
          if (($(event.target).closest('nav.yolo-canvas-menu-wrapper').length == 0)
            && ($(event.target).closest('.canvas-menu-toggle')).length == 0) {
            $('nav.yolo-canvas-menu-wrapper').removeClass('in');
        }
    });

    $('.canvas-menu-toggle').on('click', function (event) {
        event.preventDefault();
        $('nav.yolo-canvas-menu-wrapper').toggleClass('in');
    });
    $('.yolo-canvas-menu-close').on('click', function (event) {
        event.preventDefault();
        $('nav.yolo-canvas-menu-wrapper').removeClass('in');
    });
  


    /* --------------------------------------------------------------------- */
    /* MENU STICKY
    /* --------------------------------------------------------------------- */
    var header_h_o = $('.header').outerHeight();
    $(window).scroll(function () {
        var scroll = $(window).scrollTop();
        var header_h = $('.header').outerHeight();
        if($(window).width()>991){
            if (scroll > header_h) {
                $('.header').addClass('menu-fixed');
                $('body').css('padding-top',header_h_o);
                $('.header.header-style-8').removeClass('menu-fixed');
                $('body.home-sidebar').css('padding-top',0);
            } 
            if (scroll < 200) {
                $('.header').removeClass('menu-fixed');
                $('body').css('padding-top',0);
            }
        }
    });



    /* --------------------------------------------------------------------- */
    /* countdown
    /* --------------------------------------------------------------------- */
    $('[data-countdown]').each(function() {
        var $this = $(this), finalDate = $(this).data('countdown');
        $this.countdown(finalDate, function(event) {
            var fomat ='<div class="box-count box-days"><div class="number">%D</div><div class="text">Days</div></div><div class="box-count box-hours"><div class="number">%H</div><div class="text">Hrs</div></div><div class="box-count box-min"><div class="number">%M</div><div class="text">Mins</div></div><div class="box-count box-secs"><div class="number">%S</div><div class="text">Secs</div></div>';
            $this.html(event.strftime(fomat));
        });
    });


    /* --------------------------------------------------------------------- */
    /* CLICK ICON MENU
    /* --------------------------------------------------------------------- */
    $('.icon-search-menu').on('click', function (event) {
              event.preventDefault();
              $('.yolo-search-wrapper').toggleClass('show');
          });
    $('.yolo-search-wrapper .close').on('click', function (event) {
          event.preventDefault();
          $('.yolo-search-wrapper').removeClass('show');
      });



    /* --------------------------------------------------------------------- */
    /* light box
    /* --------------------------------------------------------------------- */
    function light_box() {
      $("a[rel^='prettyPhoto']").prettyPhoto();
      
      $(".gallery:first a[rel^='prettyPhoto']").prettyPhoto({animation_speed:'normal',slideshow:3000, autoplay_slideshow: true});
      $(".gallery:gt(0) a[rel^='prettyPhoto']").prettyPhoto({animation_speed:'fast',slideshow:10000, hideflash: true});

      $("#custom_content a[rel^='prettyPhoto']:first").prettyPhoto({
          custom_markup: '<div id="map_canvas" style="width:260px; height:265px"></div>',
          changepicturecallback: function(){ initialize(); }
      });

      $("#custom_content a[rel^='prettyPhoto']:last").prettyPhoto({
          custom_markup: '<div id="bsap_1259344" class="bsarocks bsap_d49a0984d0f377271ccbf01a33f2b6d6"></div><div id="bsap_1237859" class="bsarocks bsap_d49a0984d0f377271ccbf01a33f2b6d6" style="height:260px"></div><div id="bsap_1251710" class="bsarocks bsap_d49a0984d0f377271ccbf01a33f2b6d6"></div>',
          changepicturecallback: function(){ _bsap.exec(); }
      });
    }

    /* --------------------------------------------------------------------- */
    /* COUNTER
    /* --------------------------------------------------------------------- */
    function counter() {
      if (!$('.mv-number-counter').length) return;

      $('.mv-number-counter').appear(); // require jquery-appear

      $(document.body).on('appear', '.mv-number-counter', function() {
        var counter = $(this);

        if (!counter.hasClass('count-complete')) {
          counter.countTo({
            speed: 1500,
            refreshInterval: 100,
            
            onComplete: function() {
              counter.addClass('count-complete');
            }
          });
        }
      });

      $(document.body).on('disappear', '.mv-number-counter', function() {
        $(this).removeClass('count-complete');
      });
    }


    /* --------------------------------------------------------------------- */
    /* BACK TO TOP
    /* --------------------------------------------------------------------- */
    function back_top() {
        if (!$('.sn-back-to-top').length) return;

        $(window).on('scroll', function() {
          $(this).scrollTop() > 220 ? $('.sn-back-to-top').addClass('on') : $('.sn-back-to-top').removeClass('on');
        });

        $(document.body).on('click', '.sn-back-to-top', function(event) {
          event.preventDefault();

          $('html, body').animate({
            scrollTop: 0,
            queue: false
          }, 500);

          return false;
        });
      }


  
    /* --------------------------------------------------------------------- */
    /* hover mega menu
    /* --------------------------------------------------------------------- */
    var h_ul = $('.active-menu ul').height();
            $('.sub-menu-mega').css('min-height', h_ul + 'px');
      $('.mega-menu .sub-menu-mega-item').each(function () {
            $('.mega-menu .sub-menu-mega-item').on('mouseenter',function(){
                $('.mega-menu .sub-menu-mega-item.active-menu').removeClass('active-menu');
                $(this).addClass('active-menu');
                 var h_ul = $('.active-menu ul').height();
                $('.sub-menu-mega').css('min-height', h_ul + 'px');
            });
        });

    /* --------------------------------------------------------------------- */
    /* map
    /* --------------------------------------------------------------------- */
    $('.map-embed').on('click',function () {
        $('.map-embed iframe').css("pointer-events", "auto");
    });
    $( ".map-embed" ).on('mouseenter',function() {
      $('.map-embed iframe').css("pointer-events", "none"); 
    });


    /* --------------------------------------------------------------------- */
    /* sidebar shop
    /* --------------------------------------------------------------------- */
    $('.click-toggle-sidebar-filter').on('click', function (e) {
        $('.sidebar-shop-col').slideToggle("slow");
        $('.sidebar-shop-search').slideUp("slow");
    })
    $('.click-toggle-sidebar-search').on('click', function (e) {
        $('.sidebar-shop-col').slideUp("slow");
        $('.sidebar-shop-search').slideToggle("slow");
    })


    /* --------------------------------------------------------------------- */
    /* shop check out
    /* --------------------------------------------------------------------- */
    $('.showlogin').on('click', function (e) {
        $('.login').slideToggle("slow");
    })
    $('.showcoupon').on('click', function (e) {
        $('.checkout_coupon').slideToggle("slow");
    })
    /* --------------------------------------------------------------------- */
    /* create-account input 
    /* --------------------------------------------------------------------- */
    $('p.create-account input').on('click', function (e) {
        $('div.create-account').slideToggle();
    })
    /* --------------------------------------------------------------------- */
    /* payment_method_cheque
    /* --------------------------------------------------------------------- */
    $('.payment_method_cheque input').on('click', function (e) {
        $('.payment_method_cheque .payment_box').slideDown("slow");
        $('.payment_method_paypal .payment_box').slideUp("slow");
    })
    $('.payment_method_paypal input').on('click', function (e) {
        $('.payment_method_cheque .payment_box').slideUp("slow");
        $('.payment_method_paypal .payment_box').slideDown("slow");
    })


    var recent_news = $('.slick-slider');
    recent_news.slick({
      centerMode: true,
      centerPadding: '375px',
      slidesToShow: 1,
      slidesToScroll: 1,
      // variableWidth: true, // slidesToShow doesn't work, must use css to have width
      autoplay: true,
      autoplaySpeed: 4000,
      responsive: [
        {
          breakpoint: 1500,
          settings: {
            centerPadding: '200px',
            slidesToShow: 1
          }
        },
        {
          breakpoint: 1130,
          settings: {
            centerPadding: '200px',
            slidesToShow: 1
          }
        },
        {
          breakpoint: 850,
          settings: {
            centerPadding: '150px',
            slidesToShow: 1
          }
        },
        {
          breakpoint: 767,
          settings: {
            centerPadding: '0px',
            slidesToShow: 1
          }
        },
        {
          breakpoint: 500,
          settings: {
            centerPadding: '0px',
            slidesToShow: 1
          }
        },
        {
          breakpoint: 479,
          settings: {
            centerPadding: '0',
            slidesToShow: 1
          }
        },
      ]
    });

    $(window).on('load',function(){
        sofani_init_owl_carousel();
        back_top();
        counter();
        begreen_3_carousel();
        begreen_2_carousel();
        light_box();
    });

});